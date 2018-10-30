
class Parser:
    """The Parser class is a parent parser that contains the most basic parsing functions."""
    def __init__(self):
        self.current = None
        self.tokens = None

    def advance(self):
        try:
            self.current = next(self.tokens)
        except StopIteration:
            self.current = None

    def match(self, typ, value=None):
        # Skip.
        if value is None and typ is None:
            val = self.current.value
            self.advance()
            return val

        # Match type.
        if value is None and self.current.typ == typ:
            val = self.current.value
            self.advance()
            return val

        # Match literal.
        if self.current.typ == typ and self.current.value == value:
            self.advance()
            return value

        raise RuntimeError(f'Expected a {typ}( {value} ), got a {self.current.typ}( {self.current.value} ) line: {self.current.line}, column: {self.current.column}')

    def _isodate(self):
        yr, (mn, day) = self._year()
        return (yr, mn, day)

    def _year(self):
        yr = self.match('NUMBER')
        self.match('HYPHEN')
        return yr, self._month()

    def _month(self):
        mn = self.match('NUMBER')
        self.match('HYPHEN')
        return mn, self._day()

    def _day(self):
        day = self.match('NUMBER')
        return day
        