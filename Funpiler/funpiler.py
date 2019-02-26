from .scanner import Scanner
from .logic_parser import LogicParser
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

    def start(self, args):
        if args.tokenize:
            self.scan(args.tokenize)
        elif args.logic:
            self.logic(args.logic)
        else:
            print("well there is nothing else to do here.")