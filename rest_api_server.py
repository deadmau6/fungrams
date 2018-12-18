from flask import Flask
from flask_restful import Resource, Api
from LogMonitor import MongoLogApi, NodeLogApi
import json

app = Flask(__name__)
api = Api(app)

class User(Resource):
    """docstring for User"""
    def get(self):
        return {"message": "hello new user!"}

api.add_resource(User, '/')

api.add_resource(MongoLogApi, '/mongologs')

api.add_resource(NodeLogApi, '/nodelogs')

if __name__ =='__main__':
    app.run(debug=True)
        