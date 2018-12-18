class SeverityLevel:
    """The SeverityLevel extends the mongo severity to a dict object."""
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

class NodeError:
    """docstring for NodeError"""
    def __init__(self, stack=None, trace=None, name=None, code=None, compile_time=None):
        self.stack = stack
        self.trace = trace
        self.name = name
        self.code = code
        self.compile_time = compile_time
        self._is_api_error = False if trace is None else True

    def __repr__(self):
        node_error = {
            'stack': self.stack,
            'trace': self.trace,
            'name': self.name,
            'code': self.code,
            'compile_time': self.compile_time,
            '_is_api_error': self._is_api_error
        }
        return f'{node_error}'

    def header(self, status):
        if self._is_api_error:
            nm = self.stack['Name']
            return f'API: {nm} {status}'
        code = f'[{self.code}]' if self.code else ''
        return f'NODE: {self.name} {code}'

    def stack_frames(self, count):
        raw_frames = self.stack['Frames']
        frames = [f'\t|{f}' for f in raw_frames[:min(len(raw_frames), count)]]
        return '\n'.join(frames)

    def message(self):
        raw_msg = self.stack['Message']
        message = f'Raw Message: {raw_msg}'
        if self.compile_time:
            return f'{message}\n\t| Compile Time Message: {self.compile_time}'
        return message

    def error_body_format(self, status='', count=-1):
        return f'{self.header(status)}\n\t| {self.message()}\n\t| Stack Frames(5):\n{self.stack_frames(count=5)}'

    def toJSON(self):
        return {
            'stack': self.stack,
            'trace': self.trace,
            'name': self.name,
            'code': self.code,
            'compile_time': self.compile_time,
            'is_api_error': self._is_api_error
        }

class MongoLog:
    """The MongoLog class is an object representation of each parsed mongo log entry."""
    def __init__(self, line_num, timestamp, severity, component, context, message):
        self.line_num = line_num
        self.timestamp = timestamp
        self.severity = SeverityLevel(severity)
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

    def toJSON(self):
        return {
            'line_num': self.line_num,
            'timestamp': self.timestamp,
            'severity': str(self.severity), 
            'component': self.component,
            'context': self.context,
            'message': self.message
        }

class NodeLog:
    """docstring for NodeLog"""
    def __init__(self, entry_num, line_num, timestamp, level, status, msg, error):
        self.entry_num = entry_num
        self.line_num = line_num
        self.timestamp = timestamp
        self.level = level
        self.status = status if status else "UNKOWN"
        self.error = NodeError(**error)

    def __repr__(self):
        node_log = {
            'entry_num': self.entry_num,
            'line_num': self.line_num,
            'timestamp': self.timestamp,
            'level': self.level,
            'status': self.status,
            'error': self.error
        }
        return f'{node_log}'

    def time_string(self):
        hour, minuets, sec = self.timestamp[1]
        return f'{hour}:{minuets}:{sec}'

    def date_string(self):
        year, month, day = self.timestamp[0]
        return f'{year}/{month}/{day}'

    def timestamp_string(self):
        return f'Date: {self.date_string()}, Time: {self.time_string()}'

    def basic_display(self):
        return f'Entry: ({self.entry_num}, {self.line_num}), {self.timestamp_string()}, {self.level}, {self.status}'
    
    def everything_display(self):
        title = f'<--- Log Number: {self.entry_num}  Level: {self.level.upper()} Log Line Number: {self.line_num}. --->'
        body = None
        if self.level == 'error':
            body = self.error.error_body_format(status=self.status)
        return f'{title}\n{body}\n'

    def display(self, level=0):
        if level == 0:
            print(self.basic_display())
        else:
            print(self.everything_display())

    def toJSON(self):
        return {
            'entry_num': self.entry_num,
            'line_num': self.line_num,
            'timestamp': self.timestamp,
            'level': self.level,
            'status': self.status,
            'error': self.error.toJSON()
        }
