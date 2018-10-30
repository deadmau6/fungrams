import inotify.adapters
import os

class FileWatcher:
    """The Notifier class is only for Linux!

    This class uses inotify to watch a physical file.
    Depending on the read rules the notifier class can read the latest changes on the file.
    This is basically an implementation of Linux's `$ less +F /example/file.txt`. 
    """
    def __init__(self, file_path):
        self.file_path = file_path
        self.read_rules = ['IN_CLOSE_WRITE', 'IN_MODIFY']
        self.file_size = os.stat(self.f_path).st_size
        self.watcher = inotify.adapters.Inotify()

    def get_read_rules(self):
        return self.read_rules

    def add_read_rule(self, new_rule):
        self.read_rules.append(new_rule)

    def stream(self, file_queue=None):
        self.watcher.add_watch(self.file_path)
        try:
            for (_, typ, path, fname) in self.watcher.event_gen(yield_nones=False):
                if file_queue is None:
                    print(self.read_file())
                else:
                    file_queue.put(self.read_file())
                
        except KeyboardInterrupt:
            self.watcher.remove_watch(self.file_path)
            print('\nClosing watcher...')

    def read_file(self):
        data = ''
        curr_size = os.stat(self.file_path).st_size
        if curr_size <= self.file_size:
            self.file_size = curr_size
            return data

        with open(self.file_path, 'r') as f:
            if f.seekable():
                f.seek(self.file_size)
            data = f.read()
        self.file_size = curr_size
        return data
