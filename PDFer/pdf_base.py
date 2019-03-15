from .pdf_doc import PdfDoc
from .catalog import Catalog
from .font import Font
from pprint import pprint

class PdfBase:

    def __init__(self, file_name):
        self.document = PdfDoc(file_name)
        self.catalog = Catalog(self.document)
        self.fonts = {}
        self.total_pages = 0

    def create_catalog(self):
        root = self.document.get_trailer('root')
        self.catalog.setup(root)
        self.total_pages = len(self.catalog.pages)

    def _get_page(self, page_number):
        return self.catalog.get_page(page_number)

    def add_fonts(self, page_number):
        # TODO: if page_number is none maybe get all
        if page_number > self.total_pages:
            raise Exception(f"Page not found there are only {self.total_pages} pages.")

        resources = self._get_page(page_number).resources()
        font = resources.get('Font')

        if isinstance(font, tuple):
            font = self.document.get_object(font)

        for k, v in font.items():
            if k in self.fonts:
                continue
            self.fonts[k] = Font(self.document, self.document.get_object(v))

    def get_json(self, flag=None, args=None):
        if flag == 'catalog':
            return self.catalog.toJSON()
        if flag == 'page':
            return self._get_page(args).toJSON()
        if flag == 'font':
            if args and args in self.fonts:
                return self.fonts[args].toJSON()
            return {k: v.toJSON() for k, v in self.fonts.items()}
        return self.document.toJSON()