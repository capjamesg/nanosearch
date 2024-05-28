# nanosearch

Build a search engine from a website sitemap. 

## Installation

```bash
pip install nanosearch
```

## Quickstart

```python
from nanosearch import NanoSearch

engine = NanoSearch().from_sitemap('https://example.com/sitemap.xml')
results = engine.search('search query')

print(results)
```

## License

This project is licensed under an [MIT license](LICENSE).