import csv
import io
import os
import unittest
from decimal import Decimal

from py_scrapers.books import next_page_url, parse_books, parse_price, scrape, write_csv
from py_scrapers.http import Fetcher
from tests.helpers import FakeResponse, FakeSession

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return f.read()


class ParsePriceTests(unittest.TestCase):
    def test_pounds(self):
        self.assertEqual(parse_price("£51.77"), Decimal("51.77"))

    def test_other_symbols_and_spaces(self):
        self.assertEqual(parse_price(" $9.99 "), Decimal("9.99"))
        self.assertEqual(parse_price("€10"), Decimal("10"))

    def test_garbage(self):
        with self.assertRaises(ValueError):
            parse_price("free!")


class ParseBooksTests(unittest.TestCase):
    def test_first_page(self):
        books = parse_books(fixture("books_page1.html"))
        self.assertEqual(len(books), 4)
        self.assertEqual(books[0]["title"], "A Light in the Attic")
        self.assertEqual(books[0]["price"], Decimal("51.77"))
        self.assertEqual(books[3]["url"], "catalogue/sharp-objects_997/index.html")

    def test_full_title_comes_from_the_title_attribute(self):
        books = parse_books(fixture("books_page2.html"))
        self.assertEqual(books[0]["title"], "Sapiens: A Brief History of Humankind")


class PaginationTests(unittest.TestCase):
    def test_next_page_url(self):
        url = next_page_url(fixture("books_page1.html"), "http://books.example.com/index.html")
        self.assertEqual(url, "http://books.example.com/page-2.html")

    def test_last_page_has_no_next(self):
        self.assertIsNone(next_page_url(fixture("books_page2.html"), "http://books.example.com/page-2.html"))

    def make_fetcher(self):
        session = FakeSession({
            "http://books.example.com/robots.txt": FakeResponse("", 404),
            "http://books.example.com/index.html": FakeResponse(fixture("books_page1.html")),
            "http://books.example.com/page-2.html": FakeResponse(fixture("books_page2.html")),
        })
        return Fetcher(session, delay=0, sleep=lambda s: None), session

    def test_scrape_follows_pages(self):
        fetcher, session = self.make_fetcher()
        books = scrape("http://books.example.com/index.html", fetcher)
        self.assertEqual(len(books), 7)
        self.assertEqual(books[0]["url"], "http://books.example.com/catalogue/a-light-in-the-attic_1000/index.html")

    def test_page_limit(self):
        fetcher, session = self.make_fetcher()
        books = scrape("http://books.example.com/index.html", fetcher, max_pages=1)
        self.assertEqual(len(books), 4)
        self.assertNotIn("http://books.example.com/page-2.html", session.calls)


class CsvTests(unittest.TestCase):
    def test_round_trip(self):
        books = parse_books(fixture("books_page1.html"))
        out = io.StringIO()
        write_csv(books, out)
        rows = list(csv.DictReader(io.StringIO(out.getvalue())))
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[1]["title"], "Tipping the Velvet")
        self.assertEqual(rows[1]["price"], "53.74")

    def test_titles_with_commas_are_quoted(self):
        out = io.StringIO()
        write_csv([{"title": "Hello, World", "price": Decimal("1.00"), "url": "u"}], out)
        self.assertIn('"Hello, World"', out.getvalue())


if __name__ == "__main__":
    unittest.main()
