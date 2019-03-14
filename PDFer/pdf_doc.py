from .pdf_scanner import PdfScanner
from .pdf_parser import PDFParser
from .xref import XRef
from pprint import pprint

class PdfDoc:
    """Should be parent class that provides fast access to the Pdf objects.
    This access can be via the file or come from redis.
    """
    def __init__(self, fname):
        #TODO: use redis to check for existing record
        self.scanner = PdfScanner()
        self.parser = PDFParser()
        self.fname = fname
        self.xref = XRef(self.fname, self._find_xref_start())
        self.xref.create_table()

    def _find_xref_start(self):
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

    def _indirect_values(self, data):
        indirect = self.parser.parse_indirect_object(self.scanner.tokenize(str(data, 'utf-8')))
        if len(indirect['values']) == 1:
            return indirect['values'][0]
        return indirect['values']

    def get_indirect_object(self, obj_number, search_stream=False):
        data = self.xref.get_object(obj_number)

        if not search_stream:
            return self._indirect_values(data)
        
        stream_regex = re.compile(br'(.*stream[\r\n]+)(.*?)(endstream.*)', re.S)
        
        m = re.match(stream_regex, data)
        
        if m:
            match = m.groups()
            info = self._indirect_values(match[0] + match[2])
            stream = self._raw_stream(info, match[1], decode_stream)
            return info, stream

        return self._indirect_values(data)

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
