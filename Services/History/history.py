from bs4 import BeautifulSoup
from requests.exceptions import HTTPError
from pprint import pprint
import datetime as dt
import requests

class HistoryChannel:
    def __init__(self):
        self._base_url = 'https://www.history.com'

    def _page_content(self, url):
        try:
            response = requests.get(url)
            return response.content
        except HTTPError as http_error:
            raise http_error
        except Exception as e:
            raise e

    def feature_citation(self, footer):
        citation_elements = footer.find('aside', 'm-detail--citation').find_all('div', 'm-detail--citation-meta')
        citation = {}
        for element in citation_elements:
            if element.h3.text == 'Access Date':
                citation[element.h3.text] = { 'text': str(dt.datetime.today().date())}
            elif element.p.a:
                link = element.p.a.get('href')
                link = link if link.startswith('http') else f"{self._base_url}{link}"
                citation[element.h3.text] = { 'text': element.p.a.text, 'link': link }
            else:
                citation[element.h3.text] = { 'text': element.p.text }
        return citation

    def feature_body(self, body):
        body_elements = body.find_all('p')
        paragraphs = []
        for element in body_elements:
            if element.a:
                links = [link.get('href') if link.get('href').startswith('http') else f"{self._base_url}{link.get('href')}" for link in element.find_all('a')]
                paragraphs.append({'text': element.text, 'links': links})
            else:
                paragraphs.append({'text': element.text,})
        return paragraphs

    def get_feature(self, article):
        feature_content = article.find('div', 'm-detail--contents').find('div', 'l-grid--content-body')
        feature_body = self.feature_body(feature_content.find('div', 'm-detail--body'))
        feature_citation = self.feature_citation(feature_content.find('footer', 'm-detail--footer'))
        return {
            'citation': feature_citation,
            'body': feature_body,
        }

    def get_events(self, container):
        group_content = container.find_all(class_='m-card-group--content')
        elements = []
        for content in group_content:
            elements.extend(content.find_all('div', 'l-grid--item'))
        contents = [e.find('div', 'm-card--content') for e in elements]
        events = []
        for content in contents:
            year = content.find('div', 'mm-card--tdih-year')
            link = year.a.get('href')
            link = link if link.startswith('http') else f"{self._base_url}{link}"
            topic = content.find('div', 'm-card--label')
            title = content.find('h2', 'm-card--header-text')
            summary = content.find('p', 'm-card--body')
            events.append({'title':title.text, 'summary':summary.text, 'year':year.text, 'topic':topic.text, 'link': link })
        return events



    def get_history_data(self, args):
        page = self._page_content(f"{self._base_url}/this-day-in-history")
        soup = BeautifulSoup(page, 'lxml')
        #
        feature = None
        if args.featured:
            feature = self.get_feature(soup.find('article', 'm-story'))
        #
        events = None
        if args.events:
            events = self.get_events(soup.find('section', 'm-list-hub').find('phoenix-hub', 'm-card-group--container'))
        return feature, events
        
# TODO:
#class Britannica:
#    pass