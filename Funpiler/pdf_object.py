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

    def get_indirect_object(self, obj_number, search_stream=False):
        data = self.get_raw_object(obj_number, more=True)

        if not search_stream:
            return self.parser.parse_indirect_object(self.scanner.tokenize(str(data, 'utf-8')))
        
        stream_regex = re.compile(b'(.*stream\n)(.*?)(endstream.*)', re.S)
        
        match = re.match(stream_regex, data).groups()
        
        if match:
            info = self.parser.parse_indirect_object(self.scanner.tokenize(str(match[0] + match[2], 'utf-8')))
            stream = self._raw_stream(info['values'], match[1])
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
        to_unicodes = {}
        for k,v in self.fonts.items():
            if 'ToUnicode' in v:
                info, u_stream = self.get_indirect_object(v['ToUnicode'][0], search_stream=True)
                to_unicodes[k] = self.parser.parse_to_unicode(self.scanner.tokenize(u_stream))
        return to_unicodes

    def _parse_xref(self):
        with open(self.fname, 'rb') as f:
            f.seek(self.xref_start, 0)
            ref_table = f.read()
        return self.parser.parse(self.scanner.tokenize(str(ref_table, 'utf-8')))

    def _raw_stream(self, stream_info, stream_data):
        decomp_typ = None
        for item in stream_info:
            if 'Filter' in item:
                decomp_typ = item['Filter']
                break

        if decomp_typ.lower() == 'flatedecode':
            return zlib.decompress(stream_data).decode('utf-8')

        return stream_data

    def _parse_content(self, obj_number):
        """
        Acrobat Versions 4.0 and 5.0 (PDF Versions 1.3 and 1.4, respectively)
        must use “ToUnicode” mapping files that are restricted to UCS-2 (Big Endian) encoding,
        which is equivalent to UTF-16BE encoding without Surrogates.
        """
        i, stream = self.get_indirect_object(obj_number, search_stream=True)
        print(len(stream))
        return i, stream


    def _translate_text(self, bf_text, translator):
        for k in bf_text:
            yield chr(int(translator[k], 16))
