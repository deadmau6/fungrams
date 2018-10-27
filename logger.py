from LogMonitor import Scanner, MongoParser, FileWatcher
import re, os, threading, queue, time
STREAM_FILE = '/home/joe/Desktop/prgms/other/stream.txt'

def log_monitor(outq):
    F_Watch = FileWatcher(STREAM_FILE)
    F_Watch.start(outq)

def parse_log(data):
    scan = Scanner()
    #mongo = MongoParser()
    
    with open(STREAM_FILE, 'r') as f:
        if f.seekable():
            f.seek(start_index)
        print([t for t in scan.tokenize(f.read())])

if __name__ == '__main__':
    scan = Scanner()
    F_Watch = FileWatcher(STREAM_FILE)
    outq = queue.Queue()
    mon = threading.Thread(target=F_Watch.start, args=(outq,))
    mon.start()
    while True:
        line = outq.get()
        # If the queue is empty then the process stopped.
        if line is None:
            raise Exception("Shutting down...")
            # Print out server response.
        print([t for t in scan.tokenize(line)])
        time.sleep(0.1)
