from flask import Flask
from flask_restful import Resource, Api
from log_resources import MongoEP, NodeEP
from flask_cors import CORS
import json

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
api = Api(app)

class User(Resource):
    """docstring for User"""
    def get(self):
        return {"message": "hello new user!"}

api.add_resource(User, '/')

api.add_resource(MongoEP, '/mongologs')

api.add_resource(NodeEP, '/nodelogs')

if __name__ =='__main__':
    app.run(debug=True)
        