from bs4 import BeautifulSoup
from requests.exceptions import HTTPError
from .connections import Mongo
from pprint import pprint
import random
import requests
import re

class Quotes:
	"""Get famous quotes and stuff from this website: https://www.brainyquote.com/"""
	def __init__(self):
		self._base_url = 'https://www.brainyquote.com/'
		self.collection = 'QUOTES'

	def _page_content(self, extension=''):
		url = self._base_url + extension
		try:
			response = requests.get(url)
			return response.content
		except HTTPError as http_error:
			raise http_error
		except Exception as e:
			raise e

	def qotd(self):
		page = self._page_content('quote_of_the_day')
		soup = BeautifulSoup(page, 'lxml')
		container = soup.find('div', 'container bqQOTD')
		q_link = container.find('a', 'oncl_q')
		q_href = q_link.attrs['href']
		q_img = q_link.contents[0]
		qotd = q_img.attrs['alt']
		print(qotd)
		sep = qotd.rsplit('-')
		quote = sep[0].rstrip()
		author = Quotes._format_author(sep[1].lstrip())
		self._save_quote_db(author, quote)

	@staticmethod
	def _format_author(author):
		return author.rstrip().lower().replace(' ', '-')

	def quotes_by_author(self, author, printAll=False):
		au = Quotes._format_author(author)
		page = self._page_content(f'/authors/{au}-quotes')
		soup = BeautifulSoup(page, 'lxml')
		container = soup.find('div', id='quotesList')
		q_links = container.find_all('a', re.compile(r"^b-qt qt_\d* oncl_q$"))
		quotes = [link.contents[0] for link in q_links]
		if printAll:
			pprint(quotes)
		else:
			print(random.choice(quotes))
		self._append_quotes_db(au, quotes)

	def _save_quote_db(self, author, quote):
		mongo = Mongo()
		with mongo:
			collect = mongo.client.fungrams[self.collection]
			if not collect.find_one({"author": author, "quote": quote}):
				collect.insert_one({"author": author, "quote": quote})

	def _append_quotes_db(self, author, quotes):
		with Mongo() as mongo:
			collect = mongo.client.fungrams[self.collection]
			q_found = collect.find({"author": author}, { "quote": 1, "_id": -1 })
			q_insert = []
			for q in quotes:
				if q not in q_found:
					q_insert.append({"author": author, "quote": q})
			if len(q_insert) != 0:
				collect.insert_many(q_insert)
