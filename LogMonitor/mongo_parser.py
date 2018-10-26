
class SeverityLevel:

    def __init__(self, level):
        self.level = level
        self.name, self.value = self.setup(level)

    def setup(self, level):
        if level == 'I':
            return 'Informational', 2
        if level == 'W':
            return 'Warning', 3
        if level == 'E':
            return 'Error', 4
        if level == 'F':
            return 'Fatal', 5
        if level == 'D':
            return 'Debug', 1
        return 'unknown', 0

    def __str__(self):
        return f'({self.level}, {self.value}, {self.name})'

class MongoEntry:
    """docstring for MongoEntry"""
    def __init__(self, line_num, timestamp, severity, component, context, message):
        self.line_num = line_num
        self.timestamp = timestamp
        self.severity = severity
        self.component = component
        self.context = context
        self.message = message

    def get_date_string(self):
        date = self.timestamp['date']
        return f'Date: {date[0]}-{date[1]}-{date[2]}'

    def get_time_string(self):
        time = self.timestamp['time']
        return f'Time: {time[0]}:{time[1]}:{time[2]}.{time[3]}'

    def get_timestamp_string(self):
        time_style = self.timestamp['format']
        offset = self.timestamp['offset']
        return f'Timestamp:\n\tFormat: {time_style}\n\t{self.get_date_string()}\n\t{self.get_time_string()}\n\tOffset: {offset}'

    def basic_display(self):
        return f'Entry: {self.line_num}, {self.severity}, {self.component}, {self.context}'

    def everything_display(self):
        return f'{self.basic_print()}\n{self.get_timestamp_string()}\nRAW Message: {self.message}\n'

    def display(self, level=0):
        if level == 0:
            print(self.basic_display(), self.get_date_string())
        else:
            print(self.everything_display())

class MongoParser:

    def __init__(self, timestamp='iso8601-local'):
        self.time_format = timestamp
        self.current = None
        self.tokens = None
        self.entries = []

    def advance(self):
        try:
            self.current = next(self.tokens)
        except StopIteration:
            self.current = None

    def match(self, typ, value=None):
        if value is None and typ is None:
            val = self.current.value
            self.advance()
            return val

        if value is None and self.current.typ == typ:
            val = self.current.value
            self.advance()
            return val

        if self.current.typ == typ and self.current.value == value:
            self.advance()
            return value

        raise RuntimeError(f'Expected a {typ}( {value} ), got a {self.current.typ}( {self.current.value} ) line: {self.current.line}, column: {self.current.column}')

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
        return SeverityLevel(level)

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
