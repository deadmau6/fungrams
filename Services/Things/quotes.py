from bs4 import BeautifulSoup
from requests.exceptions import HTTPError
from ..connections import Mongo
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
        container = soup.find('div', 'qotd_days m_panel')
        q_link = container.find('a', 'oncl_q')
        q_href = q_link.attrs['href']
        q_img = q_link.contents[0]
        qotd = q_img.attrs['alt']
        print(qotd)
        sep = qotd.rsplit(' - ', 1)
        quote = sep[0].rstrip()
        author = sep[1].lstrip()
        self._save_quote_db(author, quote)

    @staticmethod
    def _format_author(author, space='-'):
        return author.rstrip().lower().replace(' ', space)

    def find_quotes(self, search, amount=5):
        selected = self._search_quotes(search)
        if selected == None:
            print('No option was selected.')
            return

        typ, value, href = selected 
        if typ == 'Author':
            quotes = self._quotes_author(href)
            x = min(len(quotes), amount)
            print(f"Quotes from {value}:\n")
            for q in quotes[:x]:
                print(f'"{q}"\n')
            self._append_quotes_db(value, quotes)
        else:
            quotes = self._topic_quotes(href)
            x = min(len(quotes), amount)
            print(f"Quotes from {value}:\n")
            for a,q in list(quotes.items())[:x]:
                print(f'{a}: "{q}"\n')
            self._object_quotes_db(quotes)
        
    def _search_quotes(self, search):
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

    def _quotes_author(self, href):
        page = self._page_content(href)
        soup = BeautifulSoup(page, 'lxml')
        container = soup.find('div', id='quotesList')
        q_links = container.find_all('a', re.compile(r"^b-qt qt_\d* oncl_q$"))
        quotes = [link.contents[0] for link in q_links]
        return quotes

    def _topic_quotes(self, href):
        page = self._page_content(href)
        soup = BeautifulSoup(page, 'lxml')
        container = soup.find('div', id='quotesList')
        q_links = container.find_all('a', re.compile(r"^b-qt qt_\d+ oncl_q$"))
        a_links = container.find_all('a', re.compile(r"^bq-aut qa_\d+ oncl_a$"))
        quotes = {link['class'][1].lstrip('qt_'):link.contents[0] for link in q_links}
        authors = {link['class'][1].lstrip('qa_'):link.contents[0] for link in a_links}
        complete = {authors[k]: quotes[k] for k,v in zip(quotes.keys(), authors.keys())}
        return complete

    def _save_quote_db(self, author, quote):
        normalized_author = Quotes._format_author(author)
        with Mongo() as mongo:
            collect = mongo.client.fungrams[self.collection]
            if not collect.find_one({"author": normalized_author, "quote": quote}):
                collect.insert_one({"author": normalized_author, "quote": quote})

    def _append_quotes_db(self, author, quotes):
        normalized_author = Quotes._format_author(author)
        with Mongo() as mongo:
            collect = mongo.client.fungrams[self.collection]
            q_found = collect.find({"author": normalized_author}, { "quote": 1, "_id": -1 })
            q_insert = []
            for q in quotes:
                if q not in q_found:
                    q_insert.append({"author": normalized_author, "quote": q})
            if len(q_insert) != 0:
                collect.insert_many(q_insert)

    def _object_quotes_db(self, quotes):
        with Mongo() as mongo:
            collect = mongo.client.fungrams[self.collection]
            for a,q in quotes.items():
                normalized_author = Quotes._format_author(a)
                collect.update_one(
                    {"author": normalized_author, "quote": q},
                    {"$setOnInsert":{"author": normalized_author, "quote": q}},
                    upsert=True)
