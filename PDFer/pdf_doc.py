from .pdf_scanner import PdfScanner
from .pdf_parser import PDFParser
from pprint import pprint

class PdfDoc:
    """Should be parent class that provides fast access to the Pdf objects.
    This access can be via the file or come from redis.
    """
    def __init__(self, fname):
        self.scanner = PdfScanner()
        self.parser = PDFParser()
        self.fname = fname
        #TODO: use redis to check for existing record
        self.xref_start = self._startxref(start)
        #TODO: make separate xref/trailer files.
        self.xref_table, self.trailer = self._parse_file_tail()
        self.sorted_addresses = sorted([v['byte_offset'] for k, v in self.xref_table.items()])

    def _startxref(self):
        """This finds the starting byte address of the cross reference table in a PDF. 
        """
        location = None
        with open(self.fname, 'rb') as f:
            # TODO replace the arbitrary -200 with a guarenteed length.
            f.seek(-200, 2)
            arch = f.readlines()
        count = 0
        for x in arch[::-1]:
            if count == 1:
                location = int(x[:-1], 10)
                break
            else:
                count += 1
        return location

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

    def _parse_file_tail(self):
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
