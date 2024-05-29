import concurrent.futures
import json
import re
from abc import ABC
from typing import List

import getsitemap
import numpy as np
import requests
from bs4 import BeautifulSoup
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from urllib.parse import urlparse, urljoin
import math

def retrieve_page_text(url: str) -> str:
    try:
        page = requests.get(url).text
    except requests.exceptions.RequestException as e:
        return "", "", None

    content = BeautifulSoup(page, "html.parser")

    if content.find("meta", attrs={"name": "robots", "content": "noindex"}):
        return "", "", None

    if content.title is None and content.find("h1"):
        return content.get_text().replace("\n", " ").lower(), content.find("h1").text, content
    elif content.title is None:
        return content.get_text().replace("\n", " ").lower(), "", content

    return content.get_text().replace("\n", " ").lower(), content.title.text, content

def get_links(content: BeautifulSoup, site: str) -> List[str]:
    """
    Retrieve all inlinks to the site on a given page.
    """
    links = content.find_all("a")
    links = [link["href"] for link in links if link.get("href")]
    links = [link.split("#")[0].split("?")[0] for link in links]
    links = [link for link in links if urlparse(link).netloc == urlparse(site).netloc or link.startswith("/")]
    links = [urljoin(site, link) for link in links]
    return links

class NanoSearch(ABC):
    def __init__(self) -> None:
       pass

    @classmethod
    def from_sitemap(cls, sitemap_url: str, includes: List[str] = [], excludes: List[str] = [], title_transforms: List[callable] = []) -> None:
        """
        Create an index from a sitemap.
        """
        instance = cls()
        urls = getsitemap.get_individual_sitemap(sitemap_url)
        if not urls:
            print("No sitemap found")
            return None
        
        urls = urls[sitemap_url]
        urls.sort()

        if includes:
            urls = [url for url in urls if any(re.match(include, url) for include in includes)]

        if excludes:
            urls = [url for url in urls if not any(re.match(exclude, url) for exclude in excludes)]
        
        print("Indexing", len(urls), "URLs")
        instance.sitemap_domain = urlparse(sitemap_url).netloc
        instance.sitemap_domain = "https://" + instance.sitemap_domain
        instance.title_transforms = title_transforms
        instance.create_index(urls=urls)
        return instance

    @classmethod
    def from_nanosearch_json(cls, file_path: str) -> None:
        """
        Create an index from a plain text file.
        """
        # instance should be existing object
        instance = cls()

        with open(file_path, "r") as f:
            instance.url2data = json.load(f)
            instance.urls = list(instance.url2data.keys())
        
        instance.create_index_object([data["text"] for data in instance.url2data.values()])

        return instance

    def to_nanosearch_json(self, file_name = str) -> None:
        """
        Save the data used to construct an index to a file.
        """
        with open(file_name, "w") as f:
            json.dump(self.url2data, f)

    def create_index(self, urls: str) -> None:
        pass

    def create_index_object(self, data: str) -> None:
        pass

    def search(self, query: str, n=10) -> list:
        pass

    def set_title_transforms(self, title_transforms: List[callable]) -> None:
        self.title_transforms = title_transforms


class NanoSearchTFIDF(NanoSearch):
    def __init__(self) -> None:
        self.vectorizer = TfidfVectorizer()
        self.url2data = {}
        self.urls = []

    def create_index(self, urls: str) -> None:
        """
        Create an index from a list of URLs.
        """
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results, titles, content = zip(*executor.map(retrieve_page_text, urls))

        for i, url in enumerate(urls):
            if results[i] == "":
                continue

            title = titles[i]

            if self.title_transforms:
                for transform in self.title_transforms:
                    title = transform(title)

            self.url2data[url] = {"text": results[i], "title": title, "url": url}

        self.urls = list(self.url2data.keys())
        self.create_index_object([data["text"] for data in self.url2data.values()])

    def create_index_object(self, data: str) -> None:
        self.inference = self.vectorizer.fit_transform(data)

    def search(self, query: str, n=10) -> list:
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

        return results[:n]

class NanoSearchBM25(NanoSearch):
    def __init__(self) -> None:
        self.bm25 = None
        self.url2data = {}
        self.urls = []
        self.link_graph = {}

    def create_index(self, urls: str) -> None:
        """
        Create an index from a list of URLs.
        """
        self.urls = urls

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results, titles, content = zip(*executor.map(retrieve_page_text, urls))

        for i, url in enumerate(urls):
            text = [w.lower() for w in results[i].split(" ") if w != ""]

            title = titles[i]

            if self.title_transforms:
                for transform in self.title_transforms:
                    title = transform(title)

            self.url2data[url] = {"text": text, "title": title, "url": url}
            
            for link in get_links(content[i], site=self.sitemap_domain):
                self.link_graph[link] = self.link_graph.get(link, []) + [url]

        for url, linked_from in self.link_graph.items():
            if url in self.url2data:
                self.url2data[url]["linked_from"] = len(linked_from)

        self.create_index_object([data["text"] for data in self.url2data.values()])

    def create_index_object(self, data: str) -> None:
        """
        Create an index object from the data.
        """
        self.bm25 = BM25Okapi(data)

    def search(self, query: str, n=10) -> list:
        """
        Run a BM25 search on the index.
        """

        scores = self.bm25.get_scores(query.split(" "))

        for i, url in enumerate(self.urls):
            scores[i] *= 1 + 0.1 * math.log(1 + self.url2data[url].get("linked_from", 0))

        top_n = np.argsort(scores)[::-1][:n]

        return [self.url2data[self.urls[i]] for i in top_n]
