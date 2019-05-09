"""Scrape titles and prices from the Fenwick Books catalogue."""
from .http import fetch
from .soup import make_soup


def parse_books(html):
    soup = make_soup(html)
    books = []
    for article in soup.find_all("article", class_="product_pod"):
        link = article.find("h3").find("a")
        price = article.find("p", class_="price_color").get_text(strip=True)
        books.append({"title": link["title"], "url": link["href"], "price": price})
    return books


def scrape(url, session=None):
    return parse_books(fetch(url, session))
