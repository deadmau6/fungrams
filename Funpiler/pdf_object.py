from .pdf_scanner import PdfScanner
from .pdf_parser import PDFParser

class PDFObject:

    def __init__(self, fname, start):
        self.fname = fname
        self.xref_start = start
        self.scanner = PdfScanner()
        self.parser = PDFParser()
        self.xref_table, self.trailer = self._parse_xref()
        self.sorted_addresses = sorted([v['byte_offset'] for k, v in self.xref_table.items()])
        self.catalog = {}

    def _end(self, start):
        s_index = self.sorted_addresses.index(start)
        if s_index == len(self.sorted_addresses) - 1:
            return self.xref_start
        else:
            return self.sorted_addresses[s_index + 1]


    def get_root_num(self):
        return self.trailer['root']['obj_number']

    def raw_catalog(self, more=False):
        root_num = self.trailer['root']['obj_number']
        return self.get_raw_object(root_num, more)

    def create_catalog(self):
        root_num = self.trailer['root']['obj_number']
        return self.get_indirect_object(root_num)

    def get_indirect_object(self, obj_number):
        start = self.xref_table[obj_number]['byte_offset']
        end = self._end(start)

        with open(self.fname, 'rb') as f:
            f.seek(start)
            first = f.read(end - start)
        return self.parser.parse_indirect_object(self.scanner.tokenize(str(first, 'utf-8')))

    def get_raw_object(self, obj_number, more=False):
        start = self.xref_table[obj_number]['byte_offset']
        end = self._end(start)

        with open(self.fname, 'rb') as f:
            f.seek(start)
            first = f.read(end - start)
        if more:
            return first
        return str(first, 'utf-8')

    def _parse_xref(self):
        with open(self.fname, 'rb') as f:
            f.seek(self.xref_start, 0)
            ref_table = f.read()
        return self.parser.parse(self.scanner.tokenize(str(ref_table, 'utf-8')))