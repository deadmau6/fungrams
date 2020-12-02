from .commander import Commander
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

    @property
    def is_alive(self):
        if not hasattr(self, '_is_alive'):
            self._is_alive = Commander.check_server(self.host, self.port)
        return self._is_alive

    def revive(self):
        self._is_alive = Commander.check_server(self.host, self.port)