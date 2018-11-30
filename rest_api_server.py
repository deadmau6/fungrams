from flask import Flask
from flask_restful import Resource, Api
from LogMonitor import Scanner, MongoParser, NodeParser
import json

STREAM_FILE = '/var/log/mongodb/mongod.log'
Node_File = '/home/joe/Documents/SavantX/server/logs/app.log'

app = Flask(__name__)
api = Api(app)

class User(Resource):
    """docstring for User"""
    def get(self):
        return {"message": "hello new user!"}

class Logger(Resource):
    """docstring for logger"""
    def __init__(self):
        super().__init__()
        self.scanner = Scanner()
        self.mongo = MongoParser()
        self.node = NodeParser()

    def get(self):
        logs = []
        with open(Node_File, 'r') as f:
            for entry in self.node.parse(self.scanner.tokenize(f.read())):
                logs.append(entry.toJSON())
        return logs

api.add_resource(User, '/')

api.add_resource(Logger, '/logs')

if __name__ =='__main__':
    app.run(debug=True)
        