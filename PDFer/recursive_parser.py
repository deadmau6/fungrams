
class RecursiveParser:
    """The Parser class is a parent parser that contains the most basic parsing functions."""
    def __init__(self):
        self.current = None
        self.tokens = None

    def advance(self):
        try:
            self.current = next(self.tokens)
        except StopIteration:
            self.current = None

    def match(self, kind, value=None):
        # Skip.
        if value is None and kind is None:
            val = self.current.value
            self.advance()
            return val

        # Match type.
        if value is None and self.current.kind == kind:
            val = self.current.value
            self.advance()
            return val

        # Match literal.
        if self.current.kind == kind and self.current.value == value:
            self.advance()
            return value

        raise RuntimeError(f'Expected a {kind}( {value} ), got a {self.current.kind}( {self.current.value} ) line: {self.current.line}, column: {self.current.column}')
        