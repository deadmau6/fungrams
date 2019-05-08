from scipy import ndimage
import numpy as np
import io
from .hufftable import HuffTable 
from .static import jpgIgnoreBytes

class ImageStream:

    def __init__(self, pdfdoc, image_stream):
        self._document = pdfdoc
        self.stream = image_stream
        self.color_space = image_stream.get_info('ColorSpace')
        if isinstance(self.color_space, tuple):
            # ICC might be a stream so tuple is returned
            self.color_space = self._document.get_object(self.color_space)

    def _special_color_space(self, cspace, cspace_args=None):
        # Separation, DeviceN, Indexed, Pattern
        # *NOTE* TINTS ARE SUBTRACTIVE SO 0.0 denotes lightest of a color & 1.0 is the darkest! 
        if cspace == 'indexed':
            # Allows color components to be represented in a single component
            # 
            # [/Indexed, base, hival, lookup]
            # base = a color space used to define the color table
            # hival = max iinteger range of the color table (0 < hival <= 255)
            # lookup = the color table, can be a stream or byte string
            # lookup_size = base_color_depth * (hival + 1)
            return 1
        if cspace == 'separation':
            # (see subtractive notes above)
            # Used to control processes on a single colorant like cyan and
            # this is really only used for printers/printing devices.
            # 
            # [/Separation, name, alternateSpace, tintTransform]
            # name = name object specifying the colorant (can be All or None)
            # alternateSpace = alternative color space (can be array or name object)(any non special color space)
            # tintTransform = a function used to transform tint to color
            name, alternate, tint = (None, None, None)
            for x in cspace_args:
                if isinstance(x, tuple):
                    tint = x
                elif isinstance(x, list):
                    alternate = x
                    break
                else:
                    if x.lower() in ['devicecmyk', 'devicergb', 'devicegray', 'calrgb' , 'calgray', 'lab', 'iccbased']:
                        alternate = x.lower()
                        break
                    name = x
            if isinstance(alternate, list):
                return self._color_depth(alternate)

            if alternate.startswith('device'):
                return self._device_color_space(alternate)
            
            return self._cie_color_depth(alternate)
        if cspace == 'pattern':
            # Please God No!, this one is a real shit show.
            # 
            # Types:
            # Tiling Patterns (subtypes: Color or Non-Color)
            # Shading Patterns (7 different subtypes)
            return cspace_args
        # (see subtractive notes above)
        # Whole buncha crap if there is an SubType == NChannel in attributes, totally different rules(i think)
        # AKA: len(name) = color_depth
        # name -maps-to-> alternate w\(tintTransform) THEN alternate -maps-to-> out w\(attributes(sometimes))
        # 
        # [/DeviceN, name, alternateSpace, tintTransform, attributes(optional)]
        # name = array of name objects specifying color components (can be 'None')
        # alternateSpace = alternative color space (can be array or name object)(any non special color space)
        # tintTransform = a function used to transform tint to color
        # attributes = dictionary containing extra info for custom image blending
        name, alternate, tint, attributes = (None, None, None, None)
        for x in cspace_args:
            if isinstance(x, tuple):
                tint = x
            elif isinstance(x, dict):
                attributes = x
            elif isinstance(x, list):
                is_alter = False
                for nm in x:
                    if nm.lower() in ['devicecmyk', 'devicergb', 'devicegray', 'calrgb' , 'calgray', 'lab', 'iccbased']:
                        is_alter = True
                        break
                if is_alter:
                    alternate = x
                else:
                    name = x
            else:
                alternate = x.lower()
        # I think this is the over all depth?
        return len(name)

    def _device_color_space(self, cspace, cspace_args=None):
        if cspace.endswith('gray'):
            return 1

        if cspace.endswith('rgb'):
            return 3

        if cspace.endswith('cmyk'):
            # needs its own "SPECIAL CONVERSION" maybe
            # Red = 255 * (1 - C) * (1 - K)
            # Green = 255 * (1 - M) * (1 - K)
            # Blue = 255 * (1 - Y) * (1 - K)
            return 4
        # Must be DeviceN which is actually a special color space
        return self._special_color_space(cspace, cspace_args)

    def _cie_color_space(self, cspace, cspace_args=None):
        # CalRGB,CalGray, Lab, ICCBased
        if cspace.endswith('gray'):
            return 1

        if cspace.endswith('rgb'):
            return 3

        if cspace.endswith('lab'):
            return 3

        if cspace.endswith('cmyk'):
            return 4
        
        # [/ICCBased, stream]
        # cspace_args should be indirect object
        icc_stream = self._document.get_object(cspace_args[0], search_stream=True)
        return icc_stream.get_info('N')

    def get_color_depth(self):
        # Color space can be array or name or stream
        if self.color_space is None:
            # TODO: handle JPXDecode which is the only case color space is None
            return 1

        name = None
        cs_args = None

        if isinstance(self.color_space, str):
            name = self.color_space.lower()

        elif isinstance(self.color_space, list):
            name = self.color_space[0].lower()
            if len(self.color_space) > 1:
                cs_args = self.color_space[1:]

        if name.startswith('device'):
            return self._device_color_space(name, cs_args)
        
        if name.startswith('cal') or name in ['lab', 'iccbased']:
            return self._cie_color_space(name, cs_args)

        return self._special_color_space(name, cs_args)

    def get_shape(self):
        height = self.stream.get_info('Height')
        width = self.stream.get_info('Width')
        return height, width, self.get_color_depth()

    def filter_hexcodes(self, hexList, remove):
        #Remove excess data from hexcodes
        filteredSymbols = []
        for symbol in hexList:
            
            if(symbol and symbol[0] == 'x'):
                filteredSymbols.append(symbol[1:3])
            elif not remove:
                filteredSymbols.append(symbol)
            elif remove == "replace":
                filteredSymbols.append(0)
        return filteredSymbols

    def get_hufftable(self, unfilteredSymbols, symbolNum):
        filteredSymbols = self.filter_hexcodes(unfilteredSymbols, False)
        newHuff = []
        symbolPosition = 0

        for row in symbolNum:
            symbolRow = []
            for sym in range(row):
                symbolRow.append(filteredSymbols[symbolPosition])
                symbolPosition+=1
            newHuff.append(symbolRow)

        return newHuff

    def zigzag_table(self, bytes):
        #Generate 8x8 table from array of bytes in zigzag sequence
        #base = 0 for 8 bit, base = 1 for 16 bit
        table = np.zeros((8,8), dtype=object)
        col = 0
        row = 0
        for i in range(64):
            table[row][col] = str(bytes[i])
            if((col+row) % 2 == 0):
                #Even lines go up
                if(row == 0):
                    col +=1
                elif(col == 7):
                    row +=1
                else:
                    row -=1
                    col +=1
            else:
                #Odd lines go down
                if(row == 7):
                    col +=1
                elif(col == 0):
                    row +=1
                else:
                    row +=1
                    col -=1
            
        return table

    def huffman_decode(self, bytes, huffman):
        #Take group of bytes, translate using huffman tree
        binary_concat = ''
        check_bin = ''
        translation = ''

        for byte in bytes:
            if(byte):
                binary_string = bin(int(byte, 16))[2:]
                binary_concat += binary_string

        for bit in binary_concat:
            check_bin += bit
            for h in huffman:
                for node in h:
                    if (node.code == check_bin):
                        translation += node.char
                        check_bin = ''

    def parse_jpeg(self, jpgFile):
        byteList = str(jpgFile).split('\\')
        prevByte = ''
        ac_huffList = []
        dc_huffList = []
        ac_huffTable = []
        dc_huffTable = []
        DCTList = []
        scan_markers = ()

        #Scan data stream for two byte markers indicating data segment
        for b, byte in enumerate(byteList):
            if prevByte == 'xff':
                #Headers
                if byte == 'xc0':
                    #SOF Baseline DCT
                    print('Baseline DCT')
                    precision = byteList[b+3]
                    imHeight = byteList[b+4: b+6]
                    imWidth = byteList[b+6: b+8]
                    compNum = byteList[b+8]
                    components = byteList[b+9: b+12]
                elif byte == 'xc1':
                    #SOF Extended sequential dct
                    print('Extended DCT')
                elif byte == 'xc2':
                    #SOF Progressive DCT
                    print('Progressive DCT')
                elif byte == 'xc3':
                    #SOF Lossless DCT
                    print('Lossless DCT')
                    
                #SOF Markers, differential, huffman coding
                elif byte == 'xc5':
                    #Differential sequential dct
                    print('Diff Seq DCT')
                elif byte == 'xc6':
                    print('Diff Progressive DCT')
                    #Differential progressive dct
                elif byte == 'xc7':
                    #Differential lossless
                    print('Diff Lossless DCT')

                #Huffman  
                elif byte == 'xc4':
                    #From Marker, Length = 2 bytes, HT info = 1 byte, number of symbols = 16 bytes
                    htInfo = byteList[b+3]
                    symbolList = byteList[b+4: b+20]
                    symbolNum = [int(s[1:3]) for s in symbolList]
                    #Sum of symbol_num gives remaining number of bytes, since they are the number of entries per row in the HT
                    unfilteredSymbols = byteList[b+20: b+20+sum(symbolNum)]
                    #Generate huffman table from symbols and their encoded lengths
                    newHuff = self.get_hufftable(unfilteredSymbols, symbolNum)
                    if (int(htInfo[2]) == 0):
                        dc_huffList.append(newHuff)
                    else:
                        ac_huffList.append(newHuff)

                #Quantization table
                elif byte == 'xdb':
                    QTInfo = byteList[b+2]
                    precision = (int(QTInfo[1])+1) * 64
                    unfilteredQTBytes = byteList[b+3: b+3+precision]
                    QTBytes = self.filter_hexcodes(unfilteredQTBytes, "replace")
                    QTTable = self.zigzag_table(QTBytes)

                elif byte == 'xda':
                    #SOS
                    componentInfo = []
                    length = int(byteList[b+1][1:] + byteList[b+2][1:], 16)
                    compNum = int(byteList[b+3][1:])
                    #Components are 2 bytes each, number of components specified by previous byte
                    for comp in range(compNum):
                        pos = b+4+(comp*2)
                        componentInfo.append(byteList[pos: pos+2])

                    prevHex = ''
                    marks = byteList[b:]
                    for m, mark in enumerate(marks):
                        if prevHex[:3] == 'xff':
                            if mark[:3] not in jpgIgnoreBytes:
                                #If xff is followed by a byte not in jpgIgnoreBytes, it is the end of the scan
                                eofMarker = m
                                break
                        prevHex = mark
                    scan_markers = (b, eofMarker)
                    components.append(byteList[b+length+1: eofMarker-1])

                elif byte == 'xdd':
                    #DRI
                    print("Restart Interval")

            prevByte = byte

        #Construct each huffman table
        for a in ac_huffList:
            ac_huffTable.append(HuffTable(a).generate_huff_tree())
        for d in dc_huffList:
            dc_huffTable.append(HuffTable(d).generate_huff_tree())

        #Filter bad characters out of hexcode for binary conversion
        filteredBytes = self.filter_hexcodes(byteList[scan_markers[0]: scan_markers[1]], True)
        #Huffman decoding
        self.huffman_decode(filteredBytes, dc_huffTable)

    def get_image(self):
        # This might only work because the bit depth is 8.
        # Pdf images can have differing bit depths to save space but
        # OpenCV only accepts uinsigned 8 bit integers (AKA 'uint8')
        # Coincidentally if the PDF's bit depth is 8 then it works like a charm
        # *HAVE NOT FOUND OR TESTED ON DIFFERENT BIT DEPTHS*
        shape = self.get_shape()
        img_filter = self.stream.filter.lower()

        if img_filter.startswith('dct'):
            #JPEG
            jpg_file = io.BytesIO(self.stream.decompress())
            #In house JPEG decompression run with: self.parse_jpeg(self.stream.decompress())
            return ndimage.imread(jpg_file)
        elif img_filter.startswith('flate') and self.stream.is_prediction_filter():
            # Prediction PNG/TIFF
            return np.array(self.stream.unpredict(), dtype=np.uint8).reshape(shape)

        return np.frombuffer(self.stream.decompress(), dtype=np.uint8).reshape(shape)

