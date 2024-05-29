# nanosearch

Nanosearch is an in-memory search engine designed for small (< 10,000 URL) websites.

With Nanosearch, you can build a search engine in a few lines of code.

Nanosearch supports the BM25 and TF/IDF algorithms.

Nanosearch also computes a link graph and uses the number of inlinks to a page as a ranking factor. This is useful for ranking results for queries where there are multiple relevant pages by keyword.

## Installation

```bash
pip install nanosearch
```

## Quickstart

### Build a Search Engine from a Sitemap

```python
from nanosearch import NanoSearchBM25

engine = NanoSearchBM25().from_sitemap(
    "https://jamesg.blog/sitemap.xml",
    title_transforms=[lambda x: x.split("|")[0]]
)
results = engine.search("coffee")

print(results)
```

### Build a Search Engine from a List of URLs

```python
from nanosearch import NanoSearchBM25

urls = [
    "https://jamesg.blog/",
    "https://jamesg.blog/coffee",
]

engine = NanoSearchBM25().from_urls(urls)
results = engine.search("coffee")

print(results)
```

### Save an Index to Disk

You can save an index to disk and load it later with:

```python
engine.to_nanosearch_json("index.json")

engine = NanoSearchBM25().from_nanosearch_json("index.json")
```

## Supported Algorithms

Nanosearch supports the following search algorithms:

- TF/IDF
- BM25


## License

This project is licensed under an [MIT license](LICENSE).