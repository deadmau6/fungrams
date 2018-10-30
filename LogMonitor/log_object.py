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

class NodeLog:
    """docstring for NodeLog"""
    def __init__(self, line_num, timestamp, level, status):
        self.line_num = line_num
        self.timestamp = timestamp
        self.level = level
        self.status = status
        