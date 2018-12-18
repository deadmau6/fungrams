from flask_restful import Resource, Api
from .tokens import Scanner
from .mongo_parser import MongoParser
from .node_parser import NodeParser
import json

class NodeLogApi(Resource):
    """docstring for logger"""
    def __init__(self):
        super().__init__()
        self.scanner = Scanner()
        self.node = NodeParser()
        self.file_path = '/home/joe/Documents/SavantX/server/logs/app.log'

    def get(self):
        logs = []
        with open(self.file_path, 'r') as f:
            for entry in self.node.parse(self.scanner.tokenize(f.read())):
                logs.append(entry.toJSON())
        return logs

class MongoLogApi(Resource):
    """docstring for logger"""
    def __init__(self):
        super().__init__()
        self.scanner = Scanner()
        self.mongo = MongoParser()
        self.file_path = '/var/log/mongodb/mongod.log'

    def get(self):
        logs = []
        with open(self.file_path, 'r') as f:
            for entry in self.mongo.parse(self.scanner.tokenize(f.read())):
                logs.append(entry.toJSON())
        return logs