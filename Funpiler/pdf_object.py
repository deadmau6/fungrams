from .pdf_scanner import PdfScanner
from .pdf_parser import PDFParser
from pprint import pprint
import zlib, re

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
        
        stream_regex = re.compile(b'(.*stream\n)(.*?)(endstream.*)', re.S)
        
        match = re.match(stream_regex, data).groups()
        
        if match:
            info = self.parser.parse_indirect_object(self.scanner.tokenize(str(match[0] + match[2], 'utf-8')))
            stream = self._raw_stream(info['values'], match[1], decode_stream)
            return info, stream

        return self.parser.parse_indirect_object(self.scanner.tokenize(str(data, 'utf-8')))

    def get_raw_object(self, obj_number, more=False):
        start = self.xref_table[obj_number]['byte_offset']
        end = self._end(start)

        with open(self.fname, 'rb') as f:
            f.seek(start)
            first = f.read(end - start)
        if more:
            return first
        return str(first, 'utf-8')

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
                ret_val = item['Resources'][0]
                break

            if 'Font' in item:
                fnt = item['Font']
                if isinstance(fnt, tuple):
                    fnt = self.get_indirect_object(fnt[0])['values'][0]
                break
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

        self.get_unicodes(page['Resources'][0])

        i, stream = self.get_indirect_object(page['Contents'][0], search_stream=True, decode_stream=False)

        res = self.parser.parse_content(self.scanner.b_tokenize(stream))

        text_arr = []
        for entry in res:
            font, b_arr = entry
            text_arr.append(self._decode_content(font, b_arr))
        
        return page, i, text_arr

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
        with open(self.fname, 'rb') as f:
            f.seek(self.xref_start, 0)
            ref_table = f.read()
        return self.parser.parse(self.scanner.tokenize(str(ref_table, 'utf-8')))

    def _raw_stream(self, stream_info, stream_data, decode_stream=True):
        decomp_typ = None
        for item in stream_info:
            if 'Filter' in item:
                decomp_typ = item['Filter']
                break

        if decomp_typ.lower() == 'flatedecode':
            if decode_stream:
                return zlib.decompress(stream_data).decode('utf-8')
            else:
                return zlib.decompress(stream_data)

        return stream_data

    def _parse_content(self, obj_number):
        """
        Acrobat Versions 4.0 and 5.0 (PDF Versions 1.3 and 1.4, respectively)
        must use “ToUnicode” mapping files that are restricted to UCS-2 (Big Endian) encoding,
        which is equivalent to UTF-16BE encoding without Surrogates.
        """
        i, stream = self.get_indirect_object(obj_number, search_stream=True, decode_stream=False)

        #res = self.parser.parse_content(self.scanner.b_tokenize(stream))
        #pprint(res)
        return i, stream.split(b'\n')

    def _decode_content(self, font, b_arr):
        if font in self.translation_table:
            return ''.join(self._remap(b_arr, font))

        f_encoding = self.fonts[font]['Encoding'].lower()

        if f_encoding.startswith('macroman'):
            return ''.join([str(text, 'mac_roman') for text in b_arr])

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
        
