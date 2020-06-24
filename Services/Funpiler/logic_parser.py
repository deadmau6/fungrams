from .recursive_parser import RecursiveParser

class LogicParser(RecursiveParser):

    def __init__(self):
        self.param_table = {}
        self.param_values = []

    def parse(self, tokens):
        self.tokens = tokens
        self.advance()
        return self.output(*self.prgm())

    def output(self, mode, params, expression):
        return {
            'mode': mode,
            'expression': expression,
            'param_table': self.param_table
        }

    def prgm(self):
        mode, params = self.mode()
        self.match('COLON')
        expression = self.bexpr()
        self.match('stop')
        return mode, params, expression

    def mode(self):
        modes = ['run', 'try', 'maybe']
        if self.current.kind in modes:
            mode = self.match(None)
            params = self.mode_params()
            return mode, params
        else:
            raise RuntimeError(f'Mode not specified. Allowed Modes: {modes}')

    def mode_params(self):
        if self.current.kind == 'COLON':
            return None
        self.match('ARROW')
        param_list = []
        while self.current.kind != 'ARROW':
            param_list.append(self.get_param())
            if self.current.kind == 'COMMA':
                self.match('COMMA')
        self.match('ARROW')
        return param_list

    def bexpr(self):
        be1 = self.bfactor()
        while self.current.kind == 'OR':
            op = self.match('OR')
            be2 = self.bprimary()
            be1 = (be1, op, be2)
        return be1

    def bfactor(self):
        bf1 = self.bprimary()
        while self.current.kind == 'AND':
            op = self.match('AND')
            bf2 = self.bprimary()
            bf1 = (bf1, op, bf2)
        return bf1

    def bprimary(self):
        if self.current.kind == 'ID':
            return self.var_decl()
        elif self.current.kind == 'NUMBER':
            return self.match('NUMBER')
        elif self.current.kind == 'PAREN':
            self.match('PAREN')
            b = self.bexpr()
            self.match('PAREN')
            return b
        elif self.current.kind == 'NOT':
            n = self.match('NOT')
            return n, self.bprimary()

    def get_param(self):
        if self.current.kind == 'ID':
            return self.var_decl()
        elif self.current.kind == 'NUMBER':
            val = self.match('NUMBER')
            self.param_values.append(val)
            return val

    def var_decl(self):
        var = self.match('ID')
        if var not in self.param_table:
            self.param_table[var] = self.param_values.pop(0) if self.param_values else None
        return var
