import inotify.adapters
import os

class FileWatcher:

    def __init__(self, file_path):
        self.f_path = file_path
        self.f_size = os.stat(self.f_path).st_size
        self.watcher = inotify.adapters.Inotify()

    def start(self, out_q):
        self.watcher.add_watch(self.f_path)

        print('"Ctrl-C" to end the process:')
        try:
            for event in self.watcher.event_gen(yield_nones=False):
                (_, typ, path, fname) = event
                if typ[0] == 'IN_CLOSE_WRITE':
                    out_q.put(self.read_file())
        except KeyboardInterrupt:
            print('\nExiting...')

    def read_file(self):
        curr_size = os.stat(self.f_path).st_size
        data = ''
        with open(self.f_path, 'r') as f:
            if f.seekable():
                f.seek(self.f_size)
            data = f.read()
        self.f_size = curr_size
        return data