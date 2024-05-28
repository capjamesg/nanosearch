import concurrent.futures
import re
from abc import ABC

import getsitemap
import requests
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer


def retrieve_page_text(url: str) -> str:
    content = BeautifulSoup(requests.get(url).text, "html.parser")

    return content.get_text(), content.title.text


class NanoSearch(ABC):
    def __init__(self) -> None:
        self.vectorizer = TfidfVectorizer()
        self.url2data = {}

    @classmethod
    def from_sitemap(cls, sitemap_url: str) -> None:
        """
        Create an index from a sitemap.
        """
        instance = cls()
        urls = getsitemap.retrieve_sitemap_urls(sitemap_url)
        urls.sort()
        instance.create_index(urls=urls)
        instance.urls = urls
        return instance

    def create_index(self, urls: str) -> None:
        """
        Create an index from a list of URLs.
        """
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results, titles = zip(*executor.map(retrieve_page_text, urls))

        for i, url in enumerate(urls):
            self.url2data[url] = {"text": results[i], "title": titles[i], "url": url}

        self.inference = self.vectorizer.fit_transform([data["text"] for data in self.url2data.values()])

    def search(self, query: str) -> list:
        """
        Run a TF/IDF search on the index.
        """
        query_vector = self.vectorizer.transform([query])
        cosine_similarities = self.inference.dot(query_vector.T).toarray()
        results = []

        for i in cosine_similarities.argsort(axis=0):
            item = self.url2data[self.urls[int(i)]].copy()
            item["score"] = cosine_similarities[int(i)][0]
            results.append(item)

        if "intitle:" in query:
            query = re.search(r'intitle:"(.*?)"', query).group(1)
            results = [result for result in results if query in result["title"]]
        elif "inurl:" in query:
            query = re.search(r'inurl:"(.*?)"', query).group(1)
            results = [result for result in results if query in result["url"]]

        results.sort(key=lambda x: x["score"], reverse=True)

        return results
    
