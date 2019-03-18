from .pdf_scanner import PdfScanner
from .pdf_object import PDFObject
from .pdf_base import PdfBase
from pprint import pprint
from time import time
class PDFer:
    """The PDFer is a general PDF parsing tool."""

    def __init__(self):
        self.scan = PdfScanner()
        self.fname = None

    def read_section(self, start, end):
        """This reads a section of bytes from a file and then returns a array of bytes split by 
        the newline character. 
        """
        with open(self.fname, 'rb') as f:
            f.seek(start, 0)
            if end == 0:
                sect = f.read()
            else:
                sect = f.read(abs(end - start))
        return sect.splitlines()

    def _pdf_startxref(self):
        """This finds the starting byte address of the cross reference table in a PDF. 
        """
        location = None
        with open(self.fname, 'rb') as f:
            # TODO replace the arbitrary -200 with a guarenteed length.
            f.seek(-200, 2)
            arch = f.read().splitlines()
        count = 0
        for x in arch[::-1]:
            if count == 1:
                location = int(x, 10)
                break
            else:
                count += 1
        return location

    def _start_base(self, args):
        base = PdfBase(self.fname)
        base.create_catalog()
        base.add_fonts(1)
        base.add_fonts(2)
        print('\nFONTS:\n')
        pprint(base.get_json('font'))
        print('\nPAGE TEXT:\n')
        print(base.get_page_text(1))
        print(base.get_page_text(2))

    def start(self, args):
        """This can effectively parse and access objects in a PDF."""
        if not args.file:
            print('Error! Must provide a file.')
            return

        self.fname = args.file

        if args.base:
            self._start_base(args)
            return
        
        start = self._pdf_startxref()
        print(f"Start xref: {start}")
        if args.sect:
            print("SECTION:\n")
            pprint(self.read_section(*args.sect))
            return

        pdf = PDFObject(self.fname, start)

        if args.object_number:

            if args.tokens or args.all:
                print("TOKENS:\n")
                pprint([t for t in self.scan.tokenize(pdf.get_raw_object(args.object_number))])
                print()

            if args.raw or args.all:
                print("RAW OBJECT:\n")
                if args.raw >= 2:
                    print(pdf.get_raw_object(args.object_number, more=False))
                elif args.raw == 1:
                    pprint(pdf._parse_content(args.object_number))
                else:
                    print(pdf.get_raw_object(args.object_number, more=True))
                print()
            
            if args.parsed or args.all:
                print("PARSED OBJECT:\n")
                pprint(pdf.get_indirect_object(args.object_number))
                print()
            
            if not any([args.tokens, args.raw, args.parsed]) or args.all:
                print(f"XREF ENTRY OF {args.object_number}:\n")
                pprint(pdf.xref_table[args.object_number])
        elif args.fonts:
            print("FONTS:\n")
            pprint(pdf.get_fonts(args.fonts))

        elif args.unicodes:
            print("UNICODE OBJECTS:\n")
            pprint(pdf.get_unicodes(args.unicodes))

        elif args.page_text:
            page, info, text = pdf.get_page_text(args.page_text)
            print("PAGE:\n")
            pprint(page)
            print()
            print("CONTENT INFO:\n")
            pprint(info)
            print()
            print("TEXT:\n")
            pprint(text)

        elif args.page_images:
            image_obj = pdf.get_page_images(args.page_images)
            print("IMAGES:\n")
            for k, v in image_obj.items():
                print(k)
                pprint(v['info'])

        elif args.view_image:
            obj_num = int(args.view_image[0], 10)

            if len(args.view_image) == 1:
                pdf.display_image(args.save_image, obj_num)
            else:
                for name in args.view_image[1:]:
                    pdf.display_image(args.save_image, obj_num, name)

        else:
            print("XREF TABLE:\n")
            pprint(pdf.xref_table)
            print()
            print("TRAILER:\n")
            pprint(pdf.trailer)
            print()
            print("CATALOG:\n")
            pprint(pdf.create_catalog())