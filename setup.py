import re

import setuptools
from setuptools import find_packages

with open("./nanosearch/__init__.py", "r") as f:
    content = f.read()
    # from https://www.py4u.net/discuss/139845
    version = re.search(r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]', content).group(1)

with open("README.md", "r", encoding="UTF-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nanosearch",
    version=version,
    author="capjamesg",
    author_email="readers@jamesg.blog",
    description="Build a search engine from a website sitemap.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/capjamesg/nanosearch",
    install_requires=[
        "getsitemap",
        "numpy",
        "requests",
        "beautifulsoup4",
        "rank-bm25",
        "scikit-learn",
    ],
    entry_points={"console_scripts": ["nanosearch=nanosearch.cli:cli"]},
    include_package_data=True,
    packages=find_packages(exclude=("tests",)),
    package_data={"nanosearch": ["templates/index.html"]},
    extras_require={
        "dev": [
            "flake8",
            "black==22.3.0",
            "isort",
            "twine",
            "pytest",
            "wheel",
            "mkdocs-material",
            "mkdocs",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)