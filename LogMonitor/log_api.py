from .tokens import Scanner
from .mongo_parser import MongoParser
from .node_parser import NodeParser

class LogApi:

    def __init__(self, parser_type):
        self.scanner = Scanner()
        self.parser_type = parser_type.lower()
        if self.parser_type == 'node':
            self.log_parser = NodeParser()
        else:
            self.log_parser = MongoParser()

    def parse_logs(self, log_file):
        with open(log_file, 'r') as f:
            for entry in self.log_parser.parse(self.scanner.tokenize(f.read())):
                yield entry.toJSON()

    def find_logs(self, log_file, search_filter):
        with open(log_file, 'r') as f:
            for entry in self.log_parser.parse(self.scanner.tokenize(f.read())):
                if entry.does_match(search_filter):
                    yield entry.toJSON()