from flask_restful import Resource, Api, reqparse
from flask import request
from LogMonitor import LogApi

parser = reqparse.RequestParser()
parser.add_argument('date', action='append', location='json')
parser.add_argument('time', action='append', location='json')
parser.add_argument('entry_num', location='json')
parser.add_argument('line_num', location='json')
parser.add_argument('component', location='json')
parser.add_argument('context', location='json')
parser.add_argument('level', location='json')
parser.add_argument('status', location='json')
parser.add_argument('severity', type=dict, location='json')
parser.add_argument('error', type=dict, location='json')
parser.add_argument('trace', type=dict, location='json')

class NodeEP(Resource):
    """docstring for logger"""
    def __init__(self):
        super().__init__()
        self.file_path = self.file_path = '/home/joe/Documents/SavantX/server/logs/app.log'
        self.node = LogApi('node')

    def get(self):
        logs = [x for x in self.node.parse_logs(self.file_path)]
        return logs

    def post(self):
        args = parser.parse_args()
        print(args)
        entry = [x for x in self.node.find_logs(self.file_path, args)]
        return entry

class MongoEP(Resource):
    """docstring for logger"""
    def __init__(self):
        super().__init__()
        self.file_path = '/var/log/mongodb/mongod.log'
        self.mongo = LogApi('mongo')

    def get(self):
        logs = [x for x in self.mongo.parse_logs(self.file_path)]
        return logs

    def post(self):
        args = parser.parse_args()
        print(args)
        entry = [x for x in self.mongo.find_logs(self.file_path, args)]
        return entry
