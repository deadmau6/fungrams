from .pdf_scanner import PdfScanner
from .pdf_parser import PDFParser
from .font import Font

class FontTable:
    """This is like a controller class for the fonts"""

    def __init__(self, pdfdoc):
        self._document = pdfdoc
        self.font_table = {}

    def _decode_text(self, font_name, raw_text):
        try:
            font = self.font_table[font_name]
            return font.translate(raw_text)
        except KeyError:
            raise Exception('Font does not exist?')

    def add_font(self, font):
        if font is None:
            return
        if isinstance(font, tuple):
            font = self._document.get_object(font)
        for k, v in font.items():
            if k in self.font_table:
                continue
            self.font_table[k] = Font(self._document, self._document.get_object(v))

    def decode_content(self, content_stream):
        parser = PDFParser()
        scanner = PdfScanner()

        # text_stream = { font_name: ['text', 'found', ... ] }
        text_stream = parser.parse_content(scanner.b_tokenize(content_stream.decompress()))

        text_arr = []
        
        for entry in text_stream:
            font_name, raw_text = entry
            text_arr.append(self._decode_text(font_name, raw_text))
        
        return text_arr

    def toJSON(self, font=None):
        if font and font in self.font_table:
            return { font: self.font_table[font].toJSON()}
        return {'fonts': [_ for _ in self.font_table.keys()]}
