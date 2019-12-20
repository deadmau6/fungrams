from bs4 import BeautifulSoup
from requests.exceptions import HTTPError
from .connections import Mongo
from pprint import pprint
import requests
import random
import time
import sys
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
    def _format_author(author, space='-'):
        return author.rstrip().lower().replace(' ', space)

    def quotes_by_author(self, author, printAll=True):
        selected = self.search_quotes(author)
        if selected:
            typ, value, href = selected 
            quotes = self._quotes_author(href, printAll)
            if typ == 'Author':
                self._append_quotes_db(value, quotes)
        else:
            print('No option was selected.')

    def search_quotes(self, search):
        term = Quotes._format_author(search, '+')
        page = self._page_content(f"search_results?q={term}")
        soup = BeautifulSoup(page, 'lxml')
        subnav = soup.find('div', 'subnav-below-p')
        see_also = subnav.find_all('a')
        num = range(1, len(see_also)+1)
        # ooooOO-wa-WHoa that's alot of python!
        recommended = {k: ('Author' if re.match('^/authors/.*', v['href']) else 'Topic', v.string, v['href']) for k, v in zip(num, see_also)}
        print('Please select an id number[n] from one of the following options: (or 0 to exit)')
        for i, tag in recommended.items():
            print(f"[{i}] {tag[0]}: {tag[1]}")
        selected = None
        while True:
            time.sleep(0.1)
            answer = sys.stdin.readline()
            try:
                k = int(answer)
                if k != 0:
                    selected = recommended[k]
            except (ValueError, KeyError):
                print('Please select option with the number from above. (or 0 to exit)')
            else:
                break
        return selected

    def _quotes_author(self, href, printAll=False):
        page = self._page_content(href)
        soup = BeautifulSoup(page, 'lxml')
        container = soup.find('div', id='quotesList')
        q_links = container.find_all('a', re.compile(r"^b-qt qt_\d* oncl_q$"))
        quotes = [link.contents[0] for link in q_links]
        if printAll:
          pprint(quotes)
        else:
          print(random.choice(quotes))
        return quotes

    def _save_quote_db(self, author, quote):
        with Mongo() as mongo:
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
