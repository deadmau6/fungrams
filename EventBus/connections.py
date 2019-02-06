from kazoo.client import KazooClient
from pymongo import MongoClient

__all__ = ['Mongo', 'ZooKeeper']


class ZooKeeper(object):
    """
    Context manager for ZooKeeper client connections
    """

    def __init__(self, host='localhost', port=2181):
        self._host = host
        self._port = port

    def __enter__(self):
        self._client = KazooClient(f'{self._host}:{self._port}')
        self._client.start()
        return self._client

    def __exit__(self, typ, value, traceback):
        self._client.stop()
        self._client.close()


class Mongo:
    """
    Context manager for Mongo client connections
    """

    def __init__(self, host='localhost', port=27017):
        self._client = None
        # if there are environment varibles, they will override the config
        self._host = os.environ.get('MONGO_HOST') or host
        self._port = os.environ.get('MONGO_PORT') or port

    def __enter__(self):
        self._client = MongoClient(f'mongodb://{self._host}:{self._port}', maxpoolsize=1000)
        return self._client

    def __exit__(self, type, value, traceback):
        self._client.close()
