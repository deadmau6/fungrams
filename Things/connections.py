from pymongo import MongoClient


class Mongo:
    """
    Context manager for Mongo client connections
    """
    def __init__(self, host='localhost', port='27017', db='fungrams'):
        self.host = host
        self.port = port
        self.db = db
        self.client = None

    def __enter__(self):
        self.client = MongoClient(f'mongodb://{self.host}:{self.port}')
        return self

    def __exit__(self, type, value, traceback):
        self.client.close()
