from LogMonitor import Scanner, MongoParser
import re, os

if __name__ == '__main__':
    scan = Scanner()
    mongo = MongoParser()
    filesize = os.stat('/var/log/mongodb/mongod.log').st_size
    info_logs = []
    warn_logs = []
    error_logs = []
    lcount = 0
    start_index = filesize - (filesize >> 8)
    with open('/var/log/mongodb/mongod.log', 'r') as f:
        if f.seekable():
            f.seek(start_index)

        for entry in mongo.parse(scan.tokenize(f.read()), middle_start=True):
            lcount += 1
            entry.display()
    print(lcount)