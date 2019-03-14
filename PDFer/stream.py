import zlib

class Stream:

    def __init__(self, info, data):
        self.data = data
        self.filter = info.get('Filter')
        self.f_params = info.get()