from bs4 import BeautifulSoup
from requests.exceptions import HTTPError
import requests

class Quotes:
	"""Get famous quotes and stuff from this website: https://www.brainyquote.com/"""
	def __init__(self):
		self._base_url = 'https://www.brainyquote.com/'

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
		return q_img.attrs['alt']