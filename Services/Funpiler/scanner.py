import re, collections

Token = collections.namedtuple('Token', ['kind', 'value', 'line', 'column'])

class Scanner:

    def __init__(self):
        self.keywords = {'if', 'else', 'try', 'for', 'in', 'run', 'spawn', 'stop', 'maybe'}
        self.patterns = [
            ('NUMBER', r'\d+(\.\d*)?'),
            ('OR', r'\|\|'),
            ('NOT', r'!'),
            ('AND', r'&&'),
            ('OPR', r'[/+\-*]'),
            ('DOT', r'\.'),
            ('COLON', r':'),
            ('ASSIGN', r'='),
            ('SLASH', r'/'),
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

    def tokenize(self, data):
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
            elif name == 'WHTSPC':
                continue
            yield Token(name, value, line_num, column)