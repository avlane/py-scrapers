"""Turn HTML into something searchable."""


def make_soup(html):
    from bs4 import BeautifulSoup

    return BeautifulSoup(html, "html.parser")
