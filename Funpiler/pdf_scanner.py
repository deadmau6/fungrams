import re, collections

Token = collections.namedtuple('Token', ['kind', 'value', 'line', 'column'])

class PdfScanner:

    def __init__(self):
        self.keywords = {
            'BT',
            'ET',
            'obj',
            'PDF',
            'EOF',
            'xref',
            'true',
            'null',
            'Type',
            'false',
            'stream',
            'endobj',
            'Filter',
            'Length',
            'trailer',
            'endcmap',
            'Subtype',
            'begincmap',
            'startxref',
            'endstream',
            'endbfchar',
            'beginbfchar',
            'endbfrange',
            'beginbfrange',
            'endcodespacerange',
            'begincodespacerange'
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
            ('NEWLINE', r'\r\n?|\n'),
            ('WHTSPC', r'[ \t]+'),
            ('MISMATCH', r'.'),
        ]
        self.regex = '|'.join(f"(?P<{name}>{regex})" for name, regex in self.patterns)

    def tokenize(self, data, convert_nums=True):
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
            elif name == 'NUMBER' and convert_nums:
                value = float(value) if '.' in value else int(value)
            
            yield Token(name, value, line_num, column)

    def b_tokenize(self, data):
        line_num = 1
        line_start = 0
        regs = re.compile(bytes(self.regex, 'utf-8'), re.S)
        b_keywords = [bytes(k, 'utf-8') for k in self.keywords]
        for mo in re.finditer(regs, data):
            name = mo.lastgroup
            value = mo.group(name)
            column = mo.start() - line_start
            if name == 'NEWLINE':
                line_start = mo.end()
                line_num += 1
            elif name == 'ID' and value in b_keywords:
                name = str(value, 'utf-8')
            elif name in ['ARROW','PAREN','SQUARE']:
                value = str(value, 'utf-8')
            yield Token(name, value, line_num, column)
