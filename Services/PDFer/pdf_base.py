from .pdf_doc import PdfDoc
from .catalog import Catalog
from .font_table import FontTable
from .image_stream import ImageStream
from pprint import pprint
import cv2 as cv

class PdfBase:

    def __init__(self, file_name):
        self.document = PdfDoc(file_name)
        self.catalog = Catalog(self.document)
        self.fonts = FontTable(self.document)
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
        content_stream = self._get_page(page_number).content()
        return self.fonts.decode_content(content_stream)

    def get_page_xobjects(self, page_number):
        res = self._get_page(page_number).resources()
        return res.get('XObject')

    def get_page_images(self, page_number):
        x_object = self.get_page_xobjects(page_number)
        
        if x_object is None:
            return "No images found for this page"
        
        if isinstance(x_object, tuple):
            x_object = self.document.get_object(x_object)
        
        images = {}
        
        for k,v in x_object.items():
            x_stream = self.document.get_object(v, search_stream=True)
            if x_stream.get_info('Subtype') == 'Image':
                images[k] = ImageStream(self.document, x_stream)
        return images

    def get_json(self, flag=None, args=None):
        if flag == 'catalog':
            return self.catalog.toJSON()
        if flag == 'page':
            return self._get_page(args).toJSON()
        if flag == 'font':
            return self.fonts.toJSON(args)
        return self.document.toJSON()