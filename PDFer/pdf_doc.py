from .pdf_scanner import PdfScanner
from .pdf_parser import PDFParser
from .xref import XRef
from .stream import Stream
from pprint import pprint
from os.path import abspath
import re

class PdfDoc:
    """Should be parent class that provides fast access to the Pdf objects.
    This access can be via the file or come from redis.
    """
    def __init__(self, fname):
        #TODO: use redis to check for existing record
        self.scanner = PdfScanner()
        self.parser = PDFParser()
        self.fname = abspath(fname)
        self._start = self._find_xref_start()
        t_xref, self._trailer = self._parse_file_tail()
        self.xref = XRef(self._start, self.fname, t_xref)

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

    def _parse_file_tail(self):

        end_regex = re.compile(br'^%%EOF.*?', re.S)
        
        with open(self.fname, 'rb') as f:
            f.seek(self._start, 0)
            lines = f.read().splitlines()
            ref_lines = []

            for l in lines:

                ref_lines.append(l)
                if re.match(end_regex, l):
                    break

            ref_table = b'\n'.join(ref_lines)

        xref, trailer = self.parser.parse(self.scanner.tokenize(str(ref_table, 'utf-8')))

        if 'prev' in trailer:
            self._start = trailer['prev']
            x_2, t_2 = self._parse_file_tail()
            xref.update(x_2)
            trailer.update(t_2)

        return xref, trailer

    def _indirect_values(self, data):
        indirect = self.parser.parse_indirect_object(self.scanner.tokenize(str(data, 'utf-8')))
        if len(indirect['values']) == 1:
            return indirect['values'][0]
        return indirect['values']

    def get_object(self, obj_number, search_stream=False):
        data = self.xref.get_object(obj_number)

        if not search_stream:
            return self._indirect_values(data)
        
        stream_regex = re.compile(br'(.*stream[\r\n]+)(.*?)(endstream.*)', re.S)
        
        m = re.match(stream_regex, data)
        
        if m:
            match = m.groups()
            # Currently info comes back as [{info_object}, b'\n'] where b'\n' is the empty stream from the parser.
            info = self._indirect_values(match[0] + match[2])
            return Stream(info[0], match[1])

        return self._indirect_values(data)

    def get_trailer(self, key=None):
        if key:
            return self._trailer.get(key.lower())
        return self._trailer

    def toJSON(self):
        return {
            'file': self.fname,
            'trailer': self._trailer,
            'xref': self.xref.toJSON()
        }