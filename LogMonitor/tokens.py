import collections
import re

Token = collections.namedtuple('Token', ['typ', 'value', 'line', 'column'])

class Scanner:
    """docstring for Scanner"""
    def __init__(self):
        self.keywords = {}
        self.token_specs = [
            ('NUMBER', r'\d+'),
            ('DOT', r'\.'),
            ('HYPHEN', r'\-'),
            ('STAR', r'\*'),
            ('PLUS', r'\+'),
            ('FSLASH', r'\/'),
            ('COLON', r':'),
            ('EQUALS', r'='),
            ('PIPE', r'\|'),
            ('QUOTE', r'[\'"]'),
            ('PAREN', r'[()]'),
            ('CBRACKET', r'[{}]'),
            ('SBRACKET', r'[\[\]]'),
            ('COMMA', r','),
            ('WORD', r'[A-Za-z]+'),
            ('NEWLINE', r'\n'),
            ('SKIP', r'[ \t]+'),
            ('MISMATCH', r'.'),
        ]
        self.token_regex = '|'.join(f'(?P<{name}>{regex})' for name,regex in self.token_specs)

    def tokenize(self, data):
        line_num = 1
        line_start = 0
        for mo in re.finditer(self.token_regex, data):
            name = mo.lastgroup
            value = mo.group(name)
            if name == 'NEWLINE':
                #line_start = mo.end()
                line_num += 1
            elif name =='SKIP':
                pass
            else:
                if name == 'ID' and value in self.keywords:
                    name = value
                column = mo.start() - line_start
                yield Token(name, value, line_num, column)
