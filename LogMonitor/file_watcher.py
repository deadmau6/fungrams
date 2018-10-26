import inotify.adapters
import os
STREAM_FILE = '/home/joe/Desktop/prgms/other/stream.txt'
F_SIZE = os.stat(STREAM_FILE).st_size

def read_file():
    global F_SIZE
    curr_size = os.stat(STREAM_FILE).st_size
    with open(STREAM_FILE, 'r') as f:
        if f.seekable():
            f.seek(F_SIZE)
        print(f.read())
    F_SIZE = curr_size

def monitor_file():
    f_watcher = inotify.adapters.Inotify()
    f_watcher.add_watch(STREAM_FILE)

    print('"Ctrl-C" to end the process:')
    try:
        for event in f_watcher.event_gen(yield_nones=False):
            (_, typ, path, fname) = event
            if typ[0] == 'IN_CLOSE_WRITE':
                read_file()
    except KeyboardInterrupt:
        print('\nExiting...')

class FileWatcher:

    def __init__(self, file_path):
        self.f_path = file_path
        self.f_size = os.stat(self.f_path).st_size
        self.watcher = inotify.adapters.Inotify()

    def start(self):
        self.watcher.add_watch(self.f_path)

        print('"Ctrl-C" to end the process:')
        try:
            for event in self.watcher.event_gen(yield_nones=False):
                (_, typ, path, fname) = event
                if typ[0] == 'IN_CLOSE_WRITE':
                    read_file()
        except KeyboardInterrupt:
            print('\nExiting...')