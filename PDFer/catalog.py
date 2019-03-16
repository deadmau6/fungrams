from .page import Page

class Catalog:

    def __init__(self, pdfdoc):
        self.document = pdfdoc
        self.root = None
        # The Pages index should be directly associated with the page number as follows:
        # Page_number = index + 1 therefore Page = self.pages[page_number - 1]
        self.pages = None
        self.info = {}

    def _build_page_tree(self, pages_ref):
        page_tree = self.document.get_object(pages_ref)
        
        if page_tree.pop('Type') != 'Pages':
            raise Exception('Invalid page tree node.')

        kids = page_tree.pop('Kids')

        if page_tree['Count'] == len(kids):
            return kids

        complete = []
        for k in kids:
            complete.extend(self._build_page_tree(k))
        return complete

    def setup(self, root):
        #TODO: check if catalog is of type Stream.
        catalog = self.document.get_object(root)

        # Required
        if catalog.pop('Type') != 'Catalog':
            raise Exception('Root is not a valid catalog entry.')

        self.root = root
        # Required - indirect reference
        # The Pages index should be directly associated with the page number as follows:
        # Page_number = index + 1 therefore Page = self.pages[page_number - 1] 
        self.pages = self._build_page_tree(catalog.pop('Pages'))
        # This is all optional stuff.
        # See https://www.adobe.com/content/dam/acom/en/devnet/pdf/pdf_reference_archive/pdf_reference_1-7.pdf
        # Chapter 3 Section 6.1 TABLE 3.25
        for k, v in catalog.items():
            self.info[k.lower()] = v

    def get_page(self, page_number):
        """The Pages index should be directly associated with the page number as follows:
        
        Page_number = index + 1 therefore Page = self.pages[page_number - 1]
        """
        return Page(self.document, self.document.get_object(self.pages[page_number - 1]))

    def toJSON(self):
        return {
            'root': self.root,
            'info': self.info,
            'total_pages': len(self.pages),
            'pages': self.pages
        }
