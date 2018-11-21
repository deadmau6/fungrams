from LogMonitor import Scanner, MongoParser, NodeParser, FileWatcher
from multiprocessing import Process, Queue, freeze_support
import re, os, time, signal
STREAM_FILE = '/var/log/mongodb/mongod.log'
Node_File = '/home/joe/Documents/SavantX/server/logs/app.log'
scan = Scanner()
mongo = MongoParser()
node = NodeParser()

def parse_log(data):
    print([t.basic_display() for t in mongo.parse(scan.tokenize(data))])

def parse_node():
    with open(Node_File, 'r') as f:
        for entry in node.parse(scan.tokenize(f.read())):
            entry.display(level=1)

if __name__ == '__main__':
    """
    freeze_support()
    F_Watch = FileWatcher(STREAM_FILE)
    print('"Ctrl-C" to end the process:')

    outq = Queue()
    proc = Process(target=F_Watch.watch_queue, args=(outq,)).start()
    # Set up the sinal handlers for the thread before it is created.
    signal.signal(signal.SIGTERM, FileWatcher._handle_signal)
    signal.signal(signal.SIGINT, FileWatcher._handle_signal)
    try:
        time.sleep(0.2)
        while True:
            line = outq.get()
            # If the queue is empty then the process stopped.
            if line is None:
                raise Exception("Shutting down...")
            # Print out server response.
            parse_log(line)
            time.sleep(0.1)
    except Exception as e:
        print(e)
        outq.close()
    """
    parse_node()
