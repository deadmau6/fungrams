from pymongo import MongoClient

__all__ = ['Mongo']


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
