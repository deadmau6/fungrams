from .parser import Parser
from .log_objects import MongoLog

class MongoParser(Parser):

    def __init__(self, timestamp='iso8601-local'):
        super().__init__()
        self.time_format = timestamp
        self.entries = []

    def parse(self, tokens, middle_start=False):
        self.tokens = tokens
        self.advance()
        if middle_start:
            self._skip_line()
        while self.current is not None:
            yield self._log_entry()

    def _skip_line(self):
        line_num = self.current.line
        while self.current.line == line_num:
            self.match(None)
            if self.current is None:
                break

    def _log_entry(self):
        line = self.current.line
        timestamp = self._timestamp()
        severity = self._severity()
        component = self._component()
        context = self._context()
        message = self._rawmessage()
        return MongoEntry(line, timestamp, severity, component, context, message)

    def _rawmessage(self):
        if self.current is None:
            return "empty message"
        msg = []
        line_num = self.current.line
        while self.current.line == line_num:
            msg.append(self.match(None))
            if self.current is None:
                break
        return ' '.join(msg)

    def _context(self):
        self.match('SBRACKET')
        context = []
        while self.current.typ != 'SBRACKET':
            context.append(self.match(None))
        self.match('SBRACKET')
        return ''.join(context)

    def _component(self):
        # could be an enum for sorting
        if self.current.typ == 'HYPHEN':
            self.match('HYPHEN')
            return 'UNKNOWN'

        return self.match('WORD')

    def _severity(self):
        # could be an enum for sorting
        level = self.match('WORD')
        return level

    def _timestamp(self):
        date = None
        time = None
        offset = 0
        if self.time_format == 'iso8601-local':
            date, time, offset = self._iso_local()
        elif self.time_format == 'iso8601-utc':
            date, time = self._iso_utc()
        else:
            date = self._cdate()
            time = self._time()
        return {
            'format': self.time_format,
            'date': date,
            'time': time,
            'offset': offset
        }

    def _iso_utc(self):
        date = self._isodate()
        self.match('WORD', value='T')
        time = self._time()
        self.match('WORD', value='Z')
        return date, time

    def _iso_local(self):
        date = self._isodate()
        self.match('WORD', value='T')
        time = self._time()
        self.match('HYPHEN')
        timezone = self.match('NUMBER')
        return date, time, timezone

    def _cdate(self):
        day = self.match('WORD')
        month = self.match('WORD')
        year = self.match('NUMBER')
        return (yr, mn, day)

    def _time(self):
        hr, (mi, (sec, milli)) = self._hour()
        return (hr, mi, sec, milli)

    def _hour(self):
        hr = self.match('NUMBER')
        self.match('COLON')
        return hr, self._min()

    def _min(self):
        mi = self.match('NUMBER')
        self.match('COLON')
        return mi, self._sec()

    def _sec(self):
        sec = self.match('NUMBER')
        self.match('DOT')
        return sec, self._millisec()

    def _millisec(self):
        milli = self.match('NUMBER')
        return milli
