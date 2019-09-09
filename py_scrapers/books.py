"""Scrape titles and prices from the Fenwick Books catalogue."""
import csv
from collections import namedtuple
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin

from .soup import make_soup


Book = namedtuple("Book", "title url price rating in_stock")
RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def parse_price(text):
    """'£51.77' -> Decimal('51.77')"""
    try:
        return Decimal(text.strip().lstrip("£$€").replace(",", ""))
    except InvalidOperation:
        raise ValueError("cannot read a price from {!r}".format(text))


def parse_books(html):
    soup = make_soup(html)
    books = []
    for article in soup.find_all("article", class_="product_pod"):
        link = article.find("h3").find("a")
        price = article.find("p", class_="price_color").get_text(strip=True)
        rating = 0
        for name in article.find("p", class_="star-rating")["class"]:
            rating = RATINGS.get(name, rating)
        availability = article.find("p", class_="availability").get_text(strip=True).lower()
        books.append(Book(link["title"], link["href"], parse_price(price), rating,
                          availability.startswith("in stock")))
    return books


def next_page_url(html, page_url):
    """Absolute URL of the 'next' link, or None on the last page."""
    soup = make_soup(html)
    item = soup.find("li", class_="next")
    link = item.find("a") if item else None
    return urljoin(page_url, link["href"]) if link else None


def scrape(url, fetcher, max_pages=5):
    books = []
    for _ in range(max_pages):
        html = fetcher.get(url)
        for book in parse_books(html):
            books.append(book._replace(url=urljoin(url, book.url)))
        url = next_page_url(html, url)
        if url is None:
            break
    return books


def write_csv(books, fileobj):
    writer = csv.writer(fileobj)
    writer.writerow(["title", "price", "rating", "in_stock", "url"])
    for book in books:
        writer.writerow([book.title, book.price, book.rating, "yes" if book.in_stock else "no", book.url])
