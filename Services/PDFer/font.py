from .pdf_scanner import PdfScanner
from .pdf_parser import PDFParser
from .static import glyph_dict
from pprint import pprint

class Font:

    def __init__(self, pdfdoc, font_object):
        if font_object.pop('Type') != 'Font':
            raise Exception('Incorrect format, object is not a page.')
        self._document = pdfdoc
        # Required
        self.subtype = font_object.pop('Subtype')
        self.base_font = font_object.pop('BaseFont')
        # Optional
        self.first_char = font_object.get('FirstChar')
        self.last_char = font_object.get('LastChar')
        self.widths = font_object.get('Widths')
        self.descriptor = font_object.get('FontDescriptor')
        self.encoding = font_object.get('Encoding', 'standard')
        if isinstance(self.encoding, tuple):
            self.encoding = self._document.get_object(self.encoding)
        # all of the keys will be hex strings and all the values will be readable characters.
        self.cmap = self._to_unicode_map(font_object.get('ToUnicode'))

    def _to_unicode_map(self, to_unicode):
        if to_unicode is None:
            return None

        parser = PDFParser()
        scanner = PdfScanner()

        u_stream = self._document.get_object(to_unicode, search_stream=True)
        # result (res) can have both 'bf_char' and 'bf_range'
        # TODO: handle different 'bf_codespace_range'
        res = parser.parse_to_unicode(scanner.tokenize(u_stream.decode(), convert_nums=False))
        res_cmap = res['cmap']
        # all of the keys will be hex strings and all the values will be readable characters.
        char_map = {}
        # byte-font characters (one to one) = [(key, value)]. 
        bf_chars = res_cmap.get('bf_char', [])
        
        for entry in bf_chars:
            key, val = entry
            # Converting the values(type == str):
            # format(val, '0>4') - pads the begining of the str w/ 0's to length 4 (can't remeber why? lol).
            # int(val_str, 16) - val_str is at this point a hex string so convert to hexadecimal (base 16).
            # chr(val_int) -  converts the hexadecimal to a character.
            char_map[key] = chr(int(format(val, '0>4'), 16))

        # byte-font range (many to many) or (one to one) = [(start, end, [values])]
        bf_range = res_cmap.get('bf_range', [])
        
        for entry in bf_range:

            u_start, u_end, val = entry
            # 'start' and 'end' tell us the range type i.e. (many to many)
            start = int(format(u_start, '0>4'), 16)
            end = int(format(u_end, '0>4'), 16)

            if (end - start) == 0:
                # start = end, therefore range = 1 <==> (one to one)
                char_map[u_start] = chr(int(format(val[0], '0>4'), 16))

            elif len(val) == 1:
                # start != end -> range > 1, and values = 1, therefore (many to one)? (i'll explain):
                # its actually (many to many), in this case the value is expected to increment w/ the range
                # Example: (1, 4, [a]) => if range = 1 to 4 and value = a then the cmap is:
                # cmap = { 1: 'a', 2: 'b', 3: 'c', 4: 'd' }
                val_num = int(format(val[0], '0>4'), 16)

                # we need the range to be [start, end] inclusive, in python = `range(start, end+1)`
                for i in range(start, (end + 1)):
                    # in python all hex strings start with '0x', pdf's don't so we ignore it
                    key = hex(i)[2:]
                    char_map[key] = chr(val_num)
                    # increment value
                    val_num += 1

            else:
                # range > 1, and values > 1, therefore (many to many)
                # we need the range to be [start, end] inclusive, in python = `range(start, end+1)`
                for i in range(start, (end + 1)):
                    # in python all hex strings start with '0x', pdf's don't so we ignore it
                    key = hex(i)[2:]
                    # map the range to a valid array range, EX. if start = 22 and end = 25 then:
                    # i = 22, 23, 24, 25
                    # index = 0, 1, 2, 3
                    index = i - start
                    char_map[key] = chr(int(format(val[index], '0>4'), 16))
        
        return char_map

    def _remap(self, raw_text):
        hx_arr = []
        for x in raw_text:
            try:
                hx_arr.append(x.hex())
            except Exception as e:
                # x must be a string which means it's already a hex string.
                hx_arr.append(x)

        hex_string = ''.join(hx_arr)
        text = []
        for a, b in zip(hex_string[::2], hex_string[1::2]):
            code = a+b
            if code in self.cmap:
                text.append(self.cmap[code])
            else:
                # user4369081 on stackoverflow
                text.append(bytearray.fromhex(code).decode())

        return text

    def get_diff_table(self, font):
        enc_dict = {}
        #print(font.toJSON())
        #diff_table = (font.toJSON())['encoding']['Differences']
        try:
            diff_table = (font.toJSON())['encoding']['Differences']
            #Translate to dictionary
            new_key = None
            curr_key = 0

            for enc in diff_table:
                try: 
                    int(enc)
                    new_key = enc
                except: 
                    if new_key and enc != '.notdef':
                        enc_dict.update({new_key: enc})
                        curr_key = new_key
                    elif enc != '.notdef':
                        enc_dict.update({curr_key: enc})
                    new_key = None
                    curr_key += 1
        except:
            pass
        return enc_dict

    def translate(self, raw_text, font):
        enc_dict = self.get_diff_table(font)
        if self.cmap is not None:
            return ''.join(self._remap(raw_text))

        #Identify hexcodes and replace with dictionary definition
        hex_start = str(r'\x')
        oct_start = str(r'\\')
        for i, val in enumerate(raw_text):
            if (hex_start in str(val) or oct_start in str(val)):
                #If a dictionary exists, translate, otherwise remove the reference
                if(enc_dict):
                    raw_text[i] = self.read_enc_bytes(val, enc_dict)
                else:
                    raw_text[i] = ''

        if isinstance(self.encoding, dict):
            f_encoding = self.encoding.get('BaseEncoding', 'standard').lower()
        else:
            f_encoding = self.encoding.lower()
            
        if f_encoding.startswith('mac'):
            return ''.join([str(text, 'mac_roman') if isinstance(text, bytes) else text for text in raw_text])
        
        if f_encoding.startswith('winansi'):
            return ''.join([str(text, 'cp1252') if isinstance(text, bytes) else text for text in raw_text])

        if f_encoding.startswith('standard'):
            return ''.join([str(text, 'latin_1') if isinstance(text, bytes) else text for text in raw_text])

        return ''.join([str(text, 'utf-8') if isinstance(text, bytes) else text for text in raw_text])

    def read_enc_bytes(self, text, enc_dict):
        oct = False
        hex = False
        new_string = ''
        #Scan text for hex or octal delimiter, construct new text with translated character
        for b in text:
            if (oct):
                oct = False
                if(len(text) > 2):
                    char = chr(int(str(b)[2:5], 8))
                    new_string += char
            elif ((r'\\') in str(b)):
                oct = True
            elif ((r'\x') in str(b)):
                char = chr(int(glyph_dict[enc_dict[int(str(b)[4:-1], 16)]], 16))
                new_string += char
            else:
                new_string += str(b)[2:-1]
        return (new_string)

    def toJSON(self):
        return {
            'subtype': self.subtype,
            'first_char': self.first_char,
            'last_char': self.last_char,
            'base_font': self.base_font,
            'encoding': self.encoding,
            'descriptor': self.descriptor,
            'widths': self.widths,
            'cmap': self.cmap
        }
    