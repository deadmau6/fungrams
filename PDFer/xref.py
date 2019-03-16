from .pdf_scanner import PdfScanner
from .pdf_parser import PDFParser

class XRef:
    """Holds both the xref and trailer"""

    def __init__(self, start, fname):
        self.table = None
        self.trailer = None
        self.xref_start = start
        self.fname = fname

    def create_table(self, xref=None):
        # self.table = { obj_number: (start_byte, end_byte) }
        if xref is None:
            xref, self.trailer = XRef._parse_file_tail(self.fname, self.xref_start)
        
        sorted_addresses = sorted([v['byte_offset'] for k, v in xref.items()])
        
        for k, v in xref.items():
            start = v['byte_offset']
            start_index = sorted_addresses.index(start)
            
            if s_index == len(sorted_addresses) - 1:
                self.table[k] == (start, self.xref_start)
            else:
                self.table[k] == (start, sorted_addresses[s_index + 1])

    def get_object(self, obj_number):
        """From the file, returns bytes of the object."""
        if isinstance(obj_number, tuple):
            obj_number = obj_number[0]

        start, end = self.table[obj_number]

        #TODO: check if xref table is in RAM(redis?)
        with open(self.fname, 'rb') as f:
            f.seek(start)
            data = f.read(end - start)

        return data
    
    @staticmethod
    def _parse_file_tail(fname, xref_start):
        
        pdf_parser = PDFParser()
        pdf_scan = PdfScanner()

        end_regex = re.compile(br'^%%EOF.*?', re.S)
        
        with open(fname, 'rb') as f:
            f.seek(xref_start, 0)
            lines = f.read().splitlines()
            ref_lines = []

            for l in lines:

                ref_lines.append(l)
                if re.match(end_regex, l):
                    break

            ref_table = b'\n'.join(ref_lines)

        xref, trailer = pdf_parser.parse(pdf_scan.tokenize(str(ref_table, 'utf-8')))

        if 'prev' in trailer:
            xref_start = trailer['prev']
            x_2, t_2 = XRef._parse_file_tail(fname, xref_start)
            xref.update(x_2)
            trailer.update(t_2)

        return xref, trailer
