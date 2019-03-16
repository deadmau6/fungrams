from .pdf_doc import PdfDoc
from .catalog import Catalog
from .font_table import FontTable
from pprint import pprint

class PdfBase:

    def __init__(self, file_name):
        self.document = PdfDoc(file_name)
        self.catalog = Catalog(self.document)
        self.fonts = FontTable()
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
        self.fonts.add_font(resources.get('Font'))

    def get_page_text(self, page_number):
        #TODO: make this a separate process/thread
        self.add_fonts(page_number)
        content_stream = self._get_page().content()
        return self.fonts.decode_content(content_stream)

    def get_json(self, flag=None, args=None):
        if flag == 'catalog':
            return self.catalog.toJSON()
        if flag == 'page':
            return self._get_page(args).toJSON()
        if flag == 'font':
            return self.fonts.toJSON(args)
        return self.document.toJSON()