"""Turn HTML into something searchable.

Uses BeautifulSoup when it is installed and falls back to the small tree in htmltree.py.
Both offer find, find_all, get_text and indexing, which is all the scrapers rely on.
"""


def make_soup(html):
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        from .htmltree import parse

        return parse(html)
    return BeautifulSoup(html, "html.parser")
