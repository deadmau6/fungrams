from .pdf_scanner import PdfScanner
from .pdf_parser import PDFParser
from pprint import pprint
from scipy import ndimage
from os.path import abspath
import numpy as np
import cv2 as cv
import zlib, re, io, math

class PDFObject:

    def __init__(self, fname, start):
        self.fname = fname
        self.xref_start = start
        self.scanner = PdfScanner()
        self.parser = PDFParser()
        self.xref_table, self.trailer = self._parse_xref()
        self.sorted_addresses = sorted([v['byte_offset'] for k, v in self.xref_table.items()])
        self.fonts = {}
        self.translation_table = {}
        self.catalog = {}

    def _end(self, start):
        s_index = self.sorted_addresses.index(start)
        if s_index == len(self.sorted_addresses) - 1:
            return self.xref_start
        else:
            return self.sorted_addresses[s_index + 1]

    def get_root_num(self):
        return self.trailer['root'][0]

    def raw_catalog(self, more=False):
        root_num = self.trailer['root'][0]
        return self.get_raw_object(root_num, more)

    def create_catalog(self):
        root_num = self.trailer['root'][0]
        return self.get_indirect_object(root_num)

    def get_indirect_object(self, obj_number, search_stream=False, decode_stream=True):
        data = self.get_raw_object(obj_number, more=True)

        if not search_stream:
            return self.parser.parse_indirect_object(self.scanner.tokenize(str(data, 'utf-8')))
        
        stream_regex = re.compile(br'(.*stream[\r\n]+)(.*?)(endstream.*)', re.S)
        
        m = re.match(stream_regex, data)
        
        if m:
            match = m.groups()
            info = self.parser.parse_indirect_object(self.scanner.tokenize(str(match[0] + match[2], 'utf-8')))
            stream = self._raw_stream(info['values'], match[1], decode_stream)
            return info, stream

        return self.parser.parse_indirect_object(self.scanner.tokenize(str(data, 'utf-8')))

    def get_raw_object(self, obj_number, more=False):
        start = self.xref_table[obj_number]['byte_offset']
        end = self._end(start)

        with open(self.fname, 'rb') as f:
            f.seek(start)
            data = f.read(end - start)

        if more:
            return data
        return str(data, 'utf-8')

    def get_resources(self, resource_obj):
        if isinstance(resource_obj, tuple):
            return self.get_indirect_object(resource_obj[0])['values'][0]

        if 'Resources' in resource_obj:
            return self.get_resources('Resources')

        return resource_obj 

    def get_fonts(self, obj_number):
        """Preferably start with a Resources Object"""
        if obj_number is None:
            return None

        obj = self.get_indirect_object(obj_number)
        fnt = None
        ret_val = None
        for item in obj['values']:
            # Recur to Font.
            if 'Pages' in item:
                ret_val = item['Pages'][0]
                break

            if 'Kids' in item:
                first_kid = item['Kids'][0]
                ret_val = first_kid[0]
                break

            if 'Resources' in item:
                resource = self.get_resources(item['Resources'])
                fnt = resource.get('Font')
                break

            if 'Font' in item:
                fnt = item['Font']
                break

        if isinstance(fnt, tuple):
            fnt = self.get_indirect_object(fnt[0])['values'][0]

        if fnt:
            for k, v in fnt.items():
                if k in self.fonts:
                    continue
                
                self.fonts[k] = self.get_indirect_object(v[0])['values'][0]

            return self.fonts

        return self.get_fonts(ret_val)

    def get_unicodes(self, obj_number):
        """Preferably start with a Resources Object"""
        if self.get_fonts(obj_number) is None:
            return "Error: No Fonts Found"
        
        for k,v in self.fonts.items():
            if 'ToUnicode' in v:
                info, u_stream = self.get_indirect_object(v['ToUnicode'][0], search_stream=True)
                res = self.parser.parse_to_unicode(self.scanner.tokenize(u_stream, convert_nums=False))
                self._update_translation_table(k, res['cmap'])

        return self.translation_table

    def get_page_text(self, obj_number):
        """
        Acrobat Versions 4.0 and 5.0 (PDF Versions 1.3 and 1.4, respectively)
        must use “ToUnicode” mapping files that are restricted to UCS-2 (Big Endian) encoding,
        which is equivalent to UTF-16BE encoding without Surrogates.
        """
        obj = self.get_indirect_object(obj_number)
        page = None
        for item in obj['values']:
            obj_typ = item.get('Type')
            if obj_typ == 'Page':
                page = item
                break

        if page is None:
            return "Error: please provide a page's object number."

        self.get_unicodes(obj['obj_number'])

        content = page['Contents'][0] if isinstance(page['Contents'], tuple) else page['Contents'][0][0]


        i, stream = self.get_indirect_object(content, search_stream=True, decode_stream=False)

        res = self.parser.parse_content(self.scanner.b_tokenize(stream))

        text_arr = []
        for entry in res:
            font, b_arr = entry
            text_arr.append(self._decode_content(font, b_arr))
        
        return page, i, text_arr

    def get_page_images(self, obj_number):
        obj = self.get_indirect_object(obj_number)
        page = None
        for item in obj['values']:
            obj_typ = item.get('Type')
            if obj_typ == 'Page':
                page = item
                break

        if page is None:
            return "Error: please provide a page's object number."

        x_obj = self.get_resources(page['Resources']).get('XObject')

        if x_obj is None:
            return "No images found"

        if isinstance(x_obj, tuple):
            x_obj = self.get_indirect_object(x_obj[0])['values'][0]
        
        images = {}

        for name, loc in  x_obj.items():
            i, stream = self.get_indirect_object(loc[0], search_stream=True, decode_stream=False)
            info = None
            for item in i['values']:
                sub_type = item.get('Subtype') if isinstance(item, dict) else None
                if sub_type and sub_type.lower() == 'image':
                    info = item
                    break
            if info:
                images[name] = {
                    'info': info,
                    'stream': stream
                }

        return images

    def display_image(self, save, obj_number, name=None):
        images = self.get_page_images(obj_number)
        if isinstance(images, str):
            # Images returns a str if no images are found on the page
            print(images)
            return

        # Get specific named image or just the first one
        iname, img_obj = (name, images.get(name)) if name else images.popitem()
        info = img_obj['info']
        w, h, color_space, bits_per_comp = (info['Width'], info['Height'], info.get('ColorSpace'), info.get('BitsPerComponent'))

        color_depth = self._color_depth(color_space)

        # This might only work because the bit depth is 8.
        # Pdf images can have differing bit depths to save space but
        # OpenCV only accepts uinsigned 8 bit integers (AKA 'uint8')
        # Coincidentally if the PDF's bit depth is 8 then it works like a charm
        # *HAVE NOT FOUND OR TESTED ON DIFFERENT BIT DEPTHS*
        
        img = self._convert_to_image(img_obj['stream'], (h, w, color_depth))
        cv.imshow(iname, img)
        cv.waitKey(0)
        cv.destroyAllWindows()
        if save:
            # Same as os.path.join(os.getcwd(), *path). 
            fname = abspath(f"{iname}.jpg")
            cv.imwrite(fname, img)
        return

    def _jpeg_to_image(self, jpg_stream):
        jpg_file = io.BytesIO(jpg_stream['data'])
        return ndimage.imread(jpg_file)

    def _paeth_predictor(self, left, above, upper_left):
        # Source: https://www.w3.org/TR/PNG-Filters.html
        initial_estimate = left + above - upper_left

        distance_left = abs(initial_estimate - left)
        distance_above = abs(initial_estimate - above)
        distance_upper_left = abs(initial_estimate - upper_left)
        
        if distance_left <= distance_above and distance_left <= distance_upper_left:
            return left
        elif distance_above <= distance_upper_left:
            return above
        else:
            return upper_left

    def _png_prediction(self, columns, row_size, bpp, data):
        """ Sources:
        * https://github.com/davidben/poppler/blob/master/poppler/Stream.cc
        * https://github.com/davidben/poppler
        * https://www.w3.org/TR/PNG-Filters.html
        """
        k = 0
        # initialize the prediction line to all zeros
        predline = [0] * row_size
        final = []
        while k < len(data):
            # Each row is prefaced with a 'prediction'
            curr_pred = data[k]
            # "Cut off" the prediction byte
            k += 1
            # initialize an empty up_left_buffer (only used for paeth prediction)
            up_left_buffer = [0] * (bpp + 1)
            # iterate through the row/line
            for i in range(bpp, row_size):
                # just in case
                try:
                    raw = data[k]
                    k += 1
                except Exception as e:
                    break

                # This conditional is evalulated per line/row(AKA: curr_pred shouldn't change in this for loop)
                if curr_pred == 1:
                    # PNG(1) Sub
                    predline[i] = predline[i - bpp] + raw
                elif curr_pred == 2:
                    # PNG(2) Up
                    predline[i] += raw
                elif curr_pred == 3:
                    # PNG(3) Average
                    predline[i] = ((predline[i - bpp] + predline[i]) >> 1) + raw
                elif curr_pred == 4:
                    # PNG(4) Paeth
                    # slide the up_left_buffer one over to the right
                    for j in range(bpp, 0, -1):
                        up_left_buffer[j] = up_left_buffer[j - 1]
                    # set the start of the up_left_buffer to the current
                    up_left_buffer[0] = predline[i]

                    predline[i] = self._paeth_predictor(predline[i - bpp], predline[i], up_left_buffer[bpp]) + raw
                else:
                    # PNG(0) No prediction
                    predline[i] = raw
            # Each row/line is buffered by the previous line's pixel which eqauls bpp
            final.append(predline[bpp:row_size])

        return np.array(final, dtype=np.uint8).reshape(len(final), columns, bpp)
        
    def _filtered_to_image(self, shape, params, data):
        """helpful docs = https://www.w3.org/TR/PNG-Filters.html
        Prediction Values & meanings:
        (1)  -> No prediction (defualt)
        (2)  -> TIFF predictor
        (10) -> PNG(0) No prediction on all rows 
        (11) -> PNG(1) Sub on all rows = predicts the same as the sample to the left
        (12) -> PNG(2) Up on all rows = predicts the same as the sample above
        (13) -> PNG(3) Average on all rows = predicts the avg of sample to the left and above
        (14) -> PNG(4) Paeth on all rows = nonlinear function of the sample above, left, and upper left.
        (15) -> PNG optimum (any of the above for each row)
        """
        prediction = params.get('Predictor')

        if prediction is None or prediction == 1:
            return np.frombuffer(data, dtype=np.uint8).reshape(shape)

        colors = params.get('Colors', 1)
        columns = params.get('Columns') or shape[1]

        bpc = params.get('BitsPerComponent', 8)
        n = columns * colors
        # bytes per pixel!
        bpp = (colors * bpc + 7) >> 3
        # total bytes in the prediction row/line
        row_size = ((n * bpc + 7) >> 3) + bpp
        p_index = row_size

        #TIFF
        if prediction == 2:
            return np.frombuffer(data, dtype=np.uint8).reshape(shape)

        return self._png_prediction(columns, row_size, bpp, data)

    def _convert_to_image(self, image_stream, shape):
        if isinstance(image_stream, dict):
            if image_stream['compression'] == 'dct':
                return self._jpeg_to_image(image_stream)
            elif image_stream['compression'] == 'filtered':
                return self._filtered_to_image(shape, image_stream['args'], image_stream['data'])
        
        return np.frombuffer(image_stream, dtype=np.uint8).reshape(shape)

    def _update_translation_table(self, font_key, cmap):
        char_map = {}
        bf_chars = cmap.get('bf_char', [])
        for entry in bf_chars:
            key, val = entry
            char_map[key] = chr(int(format(val, '0>4'), 16))
        
        bf_range = cmap.get('bf_range', [])
        for entry in bf_range:

            u_start, u_end, val = entry
            start = int(format(u_start, '0>4'), 16)
            end = int(format(u_end, '0>4'), 16)

            if (end - start) == 0:
                char_map[u_start] = chr(int(format(val[0], '0>4'), 16))

            elif len(val) == 1:
                val_num = int(format(val[0], '0>4'), 16)

                for i in range(start, (end + 1)):
                    key = hex(i)[2:]
                    char_map[key] = chr(val_num)
                    val_num += 1

            else:
                for i in range(start, (end + 1)):
                    key = hex(i)[2:]
                    index = i - start
                    char_map[key] = chr(int(format(val[index], '0>4'), 16))

        self.translation_table[font_key] = char_map

    def _parse_xref(self):
        end_regex = re.compile(br'^%%EOF.*?', re.S)
        with open(self.fname, 'rb') as f:
            f.seek(self.xref_start, 0)
            lines = f.read().splitlines()
            ref_lines = []
            for l in lines:
                ref_lines.append(l)
                if re.match(end_regex, l):
                    break

            ref_table = b'\n'.join(ref_lines)

        xref, trailer = self.parser.parse(self.scanner.tokenize(str(ref_table, 'utf-8')))
        if 'prev' in trailer:
            self.xref_start = trailer['prev']
            x_2, t_2 = self._parse_xref()
            xref.update(x_2)
            trailer.update(t_2)
        return xref, trailer

    def _raw_stream(self, stream_info, stream_data, decode_stream=True):
        #Watch out for FFilters and FDecodeParms
        decomp_typ = None
        params = None
        for item in stream_info:
            if 'Filter' in item:
                decomp_typ = item['Filter']
                params = item.get('DecodeParms')
                break
        
        if decomp_typ is None:
            return stream_data

        if decode_stream:
            return self._decompress_stream(stream_data, decomp_typ, params).decode('utf-8')
        
        return self._decompress_stream(stream_data, decomp_typ, params)

    def _decompress_stream(self, data, d_type, d_params):
        if isinstance(d_type, list):
            # There can be a compression pipeline
            return None

        decomp = d_type.lower()

        if decomp == 'flatedecode':
            if d_params:
                return {
                    'compression': 'filtered',
                    'args': d_params,
                    'data': zlib.decompress(data)
                }
            return zlib.decompress(data)

        if decomp == 'dctdecode':
            # For JPEGs only, DCT = Discrete Cosine Transform 
            return {
                'compression': 'dct',
                'args': d_params,
                'data': data
            }

    def _parse_content(self, obj_number):
        """
        Acrobat Versions 4.0 and 5.0 (PDF Versions 1.3 and 1.4, respectively)
        must use “ToUnicode” mapping files that are restricted to UCS-2 (Big Endian) encoding,
        which is equivalent to UTF-16BE encoding without Surrogates.
        """
        x = self.get_indirect_object(obj_number, search_stream=True, decode_stream=False)
        #res = self.parser.parse_content(self.scanner.b_tokenize(stream))
        #res = [t for t in self.scanner.b_tokenize(stream)]
        #pprint(res)
        
        return x

    def _decode_content(self, font, b_arr):
        if font in self.translation_table:
            return ''.join(self._remap(b_arr, font))

        f_encoding = self.fonts[font].get('Encoding', 'standard')
        if isinstance(f_encoding, tuple):
            fnts = self.get_indirect_object(f_encoding[0])['values'][0]
            f_encoding = fnts.get('BaseEncoding', 'standard')

        if f_encoding.startswith('mac'):
            return ''.join([str(text, 'mac_roman') for text in b_arr])
        
        if f_encoding.startswith('winansi'):
            return ''.join([str(text, 'cp1252') for text in b_arr])

        if f_encoding.startswith('standard'):
            return ''.join([str(text, 'latin_1') for text in b_arr])

        return ''.join([str(text, 'utf-8') for text in b_arr])

    def _remap(self, b_stream, font):
        hx_arr = []
        for x in b_stream:
            try:
                hx_arr.append(x.hex())
            except Exception as e:
                # x must be a string which means it's already a hex string.
                hx_arr.append(x)

        hex_string = ''.join(hx_arr)
        translator = self.translation_table[font]
        text = []
        for a, b in zip(hex_string[::2], hex_string[1::2]):
            code = a+b
            if code in translator:
                text.append(translator[code])
            else:
                # user4369081 on stackoverflow
                text.append(bytearray.fromhex(code).decode())

        return ''.join(text)

    def _color_depth(self, color_space):
        # Color space can be array or name
        if color_space is None:
            # TODO: handle JPXDecode which is the only case color space is None
            return 1

        if isinstance(color_space, tuple):
            cs_obj = self.get_indirect_object(color_space[0], search_stream=True, decode_stream=False)
            if isinstance(cs_obj, tuple):
                # ICC might be a stream so tuple is returned
                cs_obj = cs_obj[0]

            new_color_space = cs_obj['values'][0]
            return self._color_depth(new_color_space)

        name = None
        cs_args = None

        if isinstance(color_space, str):
            name = color_space.lower()

        elif isinstance(color_space, list):
            name = color_space[0].lower()
            if len(color_space) > 1:
                cs_args = color_space[1:]

        if name.startswith('device'):
            return self._device_color_space(name, cs_args)
        
        if name.startswith('cal') or name in ['lab', 'iccbased']:
            return self._cie_color_space(name, cs_args)

        return self._special_color_space(name, cs_args)

    def _device_color_space(self, color_space, cspace_args=None):
        if color_space.endswith('gray'):
            return 1

        if color_space.endswith('rgb'):
            return 3

        if color_space.endswith('cmyk'):
            # needs its own "SPECIAL CONVERSION" maybe
            # Red = 255 * (1 - C) * (1 - K)
            # Green = 255 * (1 - M) * (1 - K)
            # Blue = 255 * (1 - Y) * (1 - K)
            return 4
        # Must be DeviceN which is actually a special color space
        return self._special_color_space(color_space, cspace_args)

    def _cie_color_space(self, color_space, cspace_args=None):
        # CalRGB,CalGray, Lab, ICCBased
        if color_space.endswith('gray'):
            return 1

        if color_space.endswith('rgb'):
            return 3

        if color_space.endswith('lab'):
            return 3

        if color_space.endswith('cmyk'):
            return 4
        
        # [/ICCBased, stream]
        # cspace_args should be indirect object
        iccbased, icc_stream = self.get_indirect_object(cspace_args[0][0], search_stream=True, decode_stream=False)
        icc = iccbased['values'][0]
        return icc['N']
    
    def _special_color_space(self, color_space, cspace_args=None):
        # Separation, DeviceN, Indexed, Pattern
        # *NOTE* TINTS ARE SUBTRACTIVE SO 0.0 denotes lightest of a color & 1.0 is the darkest! 
        if color_space == 'indexed':
            # Allows color components to be represented in a single component
            # 
            # [/Indexed, base, hival, lookup]
            # base = a color space used to define the color table
            # hival = max iinteger range of the color table (0 < hival <= 255)
            # lookup = the color table, can be a stream or byte string
            # lookup_size = base_color_depth * (hival + 1)
            return 1
        if color_space == 'separation':
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
        if color_space == 'pattern':
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
        #if isinstance(alternate, list):
        #    return self._color_depth(alternate)
        #if alternate.startswith('device'):
        #    return self._device_color_space(alternate)
        #return self._cie_color_depth(alternate)
        # I think this is the over all depth?
        return len(name)
