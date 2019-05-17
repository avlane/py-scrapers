"""Scrape titles and prices from the Fenwick Books catalogue."""
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin

from .http import fetch
from .soup import make_soup


def parse_price(text):
    """'£51.77' -> Decimal('51.77')"""
    try:
        return Decimal(text.strip().lstrip("£$€"))
    except InvalidOperation:
        raise ValueError("cannot read a price from {!r}".format(text))


def parse_books(html):
    soup = make_soup(html)
    books = []
    for article in soup.find_all("article", class_="product_pod"):
        link = article.find("h3").find("a")
        price = article.find("p", class_="price_color").get_text(strip=True)
        books.append({"title": link["title"], "url": link["href"], "price": parse_price(price)})
    return books


def next_page_url(html, page_url):
    """Absolute URL of the 'next' link, or None on the last page."""
    soup = make_soup(html)
    item = soup.find("li", class_="next")
    link = item.find("a") if item else None
    return urljoin(page_url, link["href"]) if link else None


def scrape(url, session=None, max_pages=5):
    books = []
    for _ in range(max_pages):
        html = fetch(url, session)
        for book in parse_books(html):
            book["url"] = urljoin(url, book["url"])
            books.append(book)
        url = next_page_url(html, url)
        if url is None:
            break
    return books
