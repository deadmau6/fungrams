from pymongo import MongoClient

class DB_Model():

	"""docstring for ClassName"""
	def __init__(self, arg):
		#
		self.client = MongoClient('localhost', 27017)
		self.db = client.other
		self.collection = db.schedule

	def create(self, obj):
		self.collection.insert_one(obj)