from bs4 import BeautifulSoup
from requests.exceptions import HTTPError
from pprint import pprint
import datetime as dt
import requests
from pprint import pprint

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

    def feature_title(self, content):
        feature_year = content.find('p', 'tdih-featured__year')
        feature_title = content.find('span', 'tdih-featured__title')
        return f"{feature_year.text}  {feature_title.text}"

    def feature_citation(self, footer):
        citation_elements = footer.find('aside', 'article-sources').find_all('div', 'article-sources__pair')
        citation = {}
        for element in citation_elements:
            title = element.dt.text
            if title == 'URL':
                link = element.dd.a.get('href')
                link = link if link.startswith('http') else f"{self._base_url}{link}"
                citation[title] = { 'text': element.dd.a.text, 'link': link }
            else:
                description = element.dd.text
                citation[title] = { 'text': description }
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

    def get_feature_data(self, article):
        #
        featured_content = article.find('div', 'tdih-featured')
        title_content = featured_content.find('div', 'tdih-featured__content').find('div', 'featured-content-card')
        feature_title = self.feature_title(title_content)
        #
        article_content = article.find('div', 'article-content-box')
        body_content = article_content.find('div', 'article-content')
        feature_body = self.feature_body(body_content)
        #
        footer_content = article_content.find('footer', 'article-footer')
        feature_citation = self.feature_citation(footer_content)
        return {
            'title': feature_title,
            'citation': feature_citation,
            'body': feature_body,
        }

    def get_feature(self, feature_content):
        content = feature_content.find('div', 'tdih-featured__content').find('div', 'featured-content-card')
        link = content.find('a', 'featured-content-card__link')
        feature_link = link.get('href') if link.get('href').startswith('http') else f"{self._base_url}{link.get('href')}"
        #
        feature_page = self._page_content(feature_link)
        feature_soup = BeautifulSoup(feature_page, 'lxml')
        return self.get_feature_data(feature_soup.find('article', 'article'))

    def get_events(self, container):
        group_content = container.find_all(class_='tdih-posts-grid__article')
        events = []
        for content in group_content:
            year = content.find('span', 'tdih-posts-grid__article-year').text
            article_link = content.find('a', 'tdih-posts-grid__article-link')
            title = article_link.text
            link = article_link.get('href')
            link = link if link.startswith('http') else f"{self._base_url}{link}"
            topic_content = content.find('a', 'tdih-posts-grid__article-meta')
            topic = getattr(topic_content, 'text') if hasattr(topic_content, 'text') else "Other"
            events.append({ 'title':title, 'year':year, 'topic': topic, 'link': link })
        return events

    def get_history_data(self, args):
        page = self._page_content(f"{self._base_url}/this-day-in-history")
        soup = BeautifulSoup(page, 'lxml')
        #
        feature = None
        if args.featured:
            feature = self.get_feature(soup.find('div', 'tdih-featured'))
        #
        events = None
        if args.events:
            events = self.get_events(soup.find('div', 'tdih-posts').find('div', 'tdih-posts-grid'))
        return feature, events
        
# TODO:
#class Britannica:
#    pass