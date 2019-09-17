import csv
import io
import os
import unittest
from decimal import Decimal

from py_scrapers.books import Book, compare_prices, next_page_url, parse_books, parse_price, read_csv, scrape, write_csv
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

    def test_thousands_separator(self):
        self.assertEqual(parse_price("£1,051.77"), Decimal("1051.77"))

    def test_garbage(self):
        with self.assertRaises(ValueError):
            parse_price("free!")


class ParseBooksTests(unittest.TestCase):
    def test_first_page(self):
        books = parse_books(fixture("books_page1.html"))
        self.assertEqual(len(books), 4)
        self.assertEqual(books[0].title, "A Light in the Attic")
        self.assertEqual(books[0].price, Decimal("51.77"))
        self.assertEqual(books[3].url, "catalogue/sharp-objects_997/index.html")

    def test_rating_and_stock(self):
        books = parse_books(fixture("books_page1.html"))
        self.assertEqual([b.rating for b in books], [3, 1, 1, 4])
        self.assertEqual([b.in_stock for b in books], [True, True, False, True])

    def test_expensive_book_on_page_two(self):
        books = parse_books(fixture("books_page2.html"))
        self.assertEqual(books[1].price, Decimal("1051.77"))

    def test_full_title_comes_from_the_title_attribute(self):
        books = parse_books(fixture("books_page2.html"))
        self.assertEqual(books[0].title, "Sapiens: A Brief History of Humankind")


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
        self.assertEqual(books[0].url, "http://books.example.com/catalogue/a-light-in-the-attic_1000/index.html")

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
        self.assertEqual(rows[2]["in_stock"], "no")
        self.assertEqual(rows[3]["rating"], "4")

    def test_titles_with_commas_are_quoted(self):
        out = io.StringIO()
        write_csv([Book("Hello, World", "u", Decimal("1.00"), 3, True)], out)
        self.assertIn('"Hello, World"', out.getvalue())


class CompareTests(unittest.TestCase):
    def test_read_csv_round_trip(self):
        out = io.StringIO()
        write_csv(parse_books(fixture("books_page1.html")), out)
        prices = read_csv(io.StringIO(out.getvalue()))
        self.assertEqual(prices["Soumission"], Decimal("50.10"))

    def test_compare(self):
        old = {"A": Decimal("10"), "B": Decimal("5"), "C": Decimal("1")}
        new = {"A": Decimal("9"), "B": Decimal("5"), "D": Decimal("2")}
        changed, added, removed = compare_prices(old, new)
        self.assertEqual(changed, [("A", Decimal("10"), Decimal("9"))])
        self.assertEqual(added, ["D"])
        self.assertEqual(removed, ["C"])


if __name__ == "__main__":
    unittest.main()
