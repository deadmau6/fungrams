import re, collections

Token = collections.namedtuple('Token', ['kind', 'value', 'line', 'column'])

class PdfScanner:

    def __init__(self):
        self.keywords = {
            'xref',
            'startxref',
            'trailer',
            'PDF',
            'EOF',
            'Length',
            'Filter',
            'obj',
            'endobj',
            'stream',
            'endstream',
            'Type',
            'Subtype',
            'null',
            'true',
            'false'
        }
        self.patterns = [
            ('NUMBER', r'\d+(\.\d*)?'),
            ('OPR', r'[/+\-*]'),
            ('COLON', r':'),
            ('ASSIGN', r'='),
            ('PERCENT', r'%'),
            ('QUOTE', r'[\'"]'),
            ('ARROW', r'[<>]'),
            ('PAREN', r'[()]'),
            ('CURLY', r'[{}]'),
            ('SQUARE', r'[\[\]]'),
            ('COMMA', r','),
            ('ID', r'[A-Za-z]+'),
            ('NEWLINE', r'\n'),
            ('WHTSPC', r'[ \t]+'),
            ('MISMATCH', r'.'),
        ]
        self.regex = '|'.join(f"(?P<{name}>{regex})" for name, regex in self.patterns)

    def tokenize(self, data, white_space=False):
        line_num = 1
        line_start = 0
        for mo in re.finditer(self.regex, data):
            name = mo.lastgroup
            value = mo.group(name)
            column = mo.start() - line_start
            if name == 'NEWLINE':
                line_start = mo.end()
                line_num += 1
            elif name == 'ID' and value in self.keywords:
                name = value
            elif name == 'NUMBER':
                value = float(value) if '.' in value else int(value)
            #elif name == 'WHTSPC' and  not white_space:
            #    continue
            yield Token(name, value, line_num, column)