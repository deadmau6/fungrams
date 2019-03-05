from .scanner import Scanner
from .logic_parser import LogicParser
from .pdf_scanner import PdfScanner
from .pdf_object import PDFObject
from pprint import pprint

class Funpiler:
    """The Funpiler is a generic compiler that will hopefully be able to run multiple languages."""

    def __init__(self):
        self.scanner = Scanner()

    def scan(self, code):
        """This will take any string and print out the tokens generated."""
        for token in self.scanner.tokenize(code):
            print(token)

    def logic(self, code):
        """This will parse boolean logic given the proper grammer."""
        parser = LogicParser()
        pprint(parser.parse(self.scanner.tokenize(code)))

    @staticmethod
    def read_section(fname, start, end):
        """This reads a section of bytes from a file and then returns a array of bytes split by 
        the newline character. 
        """
        with open(fname, 'rb') as f:
            f.seek(start, 0)
            sect = f.read(end - start)
        return sect.split(b'\n')

    @staticmethod
    def _pdf_startxref(fname):
        """This finds the starting byte address of the cross reference table in a PDF. 
        """
        location = None
        if not fname:
            print('File name required.')
            return
        with open(fname, 'rb') as f:
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

    def start_pdf(self, args):
        """This can effectively parse and access objects in a PDF.
        """
        start = Funpiler._pdf_startxref(args.file)
        pdf = PDFObject(args.file, start)
        pdf_scan = PdfScanner()

        if args.object_number:

            if args.tokens or args.all:
                print("TOKENS:\n")
                pprint([t for t in pdf_scan.tokenize(pdf.get_raw_object(args.object_number))])
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
            print()

        elif args.sect:
            print("SECTION:\n")
            pprint(Funpiler.read_section(args.file, *args.sect))

        else:
            print("XREF TABLE:\n")
            pprint(pdf.xref_table)
            print()
            print("TRAILER:\n")
            pprint(pdf.trailer)
            print()
            print("CATALOG:\n")
            pprint(pdf.create_catalog())

    def start(self, args):
        if args.tokenize:
            self.scan(args.tokenize)
        elif args.logic:
            self.logic(args.logic)
        else:
            print("well there is nothing else to do here.")