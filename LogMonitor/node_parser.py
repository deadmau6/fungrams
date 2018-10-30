from .parser import Parser
from .log_objects import NodeLog

class NodeParser(Parser):

    def __init__(self):
        super().__init__()

    def _skip_line(self):
        line_num = self.current.line
        while self.current.line == line_num:
            self.match(None)
            if self.current is None:
                break

    def parse(self, tokens):
        self.tokens = tokens
        self.advance()
        while self.current is not None:
            yield self._log_entry()

    def _log_entry(self):
        line = self.current.line
        timestamp = self._timestamp()
        level = self._level()
        status = self._http_status()
        message = self._node_message()
        trace = self._trace()
        stack = self._stack()

    def _node_message(self):
        if self.current is None:
            return "empty message"
        msg = []
        line_num = self.current.line
        while self.current.line == line_num:
            msg.append(self.match(None))
            if self.current is None:
                break
        return ' '.join(msg)

    def _http_status(self):
        if self.current.typ == 'COLON':
            return "UNKNOWN"
        self.match('SBRACKET')
        stat = self.match('NUMBER')
        self.match('SBRACKET')
        return stat

    def _level(self):
        return self.match('WORD')

    def _timestamp(self):
        date = self._isodate()
        time = self._ntime()
        return (date, time)

    def _ntime(self):
        hr, (mi, sec) = self._nhour()
        return (hr, mi, sec)

    def _nhour(self):
        hr = self.match('NUMBER')
        self.match('COLON')
        return hr, self._nminute()

    def _nminute(self):
        mi = self.match('NUMBER')
        self.match('COLON')
        return mi, self._nsec()

    def _nsec(self):
        return self.match('NUMBER')
