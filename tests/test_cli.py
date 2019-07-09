import io
import os
import tempfile
import unittest

from py_scrapers import cli
from py_scrapers.http import Fetcher
from tests.helpers import FakeResponse, FakeSession

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return f.read()


def fetcher_for(responses):
    responses = dict(responses)
    responses.setdefault("http://books.example.com/robots.txt", FakeResponse("", 404))
    return Fetcher(FakeSession(responses), delay=0, sleep=lambda s: None)


class BooksCommandTests(unittest.TestCase):
    def setUp(self):
        self.fetcher = fetcher_for({
            "http://books.example.com/index.html": FakeResponse(fixture("books_page1.html")),
            "http://books.example.com/page-2.html": FakeResponse(fixture("books_page2.html")),
        })

    def test_prints_prices(self):
        out = io.StringIO()
        code = cli.main(["books", "http://books.example.com/index.html"], self.fetcher, out)
        self.assertEqual(code, 0)
        lines = out.getvalue().splitlines()
        self.assertEqual(len(lines), 4)
        self.assertIn("51.77  A Light in the Attic", lines[0])

    def test_pages_option(self):
        out = io.StringIO()
        cli.main(["books", "http://books.example.com/index.html", "--pages", "2"], self.fetcher, out)
        self.assertEqual(len(out.getvalue().splitlines()), 7)

    def test_csv_option(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "books.csv")
            out = io.StringIO()
            cli.main(["books", "http://books.example.com/index.html", "--csv", path], self.fetcher, out)
            with open(path, encoding="utf-8") as f:
                self.assertEqual(len(f.read().splitlines()), 5)
            self.assertIn("Wrote 4 books", out.getvalue())


class WeatherCommandTests(unittest.TestCase):
    def test_weather(self):
        fetcher = fetcher_for({"http://weather.example.com/harlow": FakeResponse(fixture("weather.html"))})
        out = io.StringIO()
        code = cli.main(["weather", "http://weather.example.com/harlow"], fetcher, out)
        self.assertEqual(code, 0)
        self.assertIn("Sunny intervals", out.getvalue())

    def test_weather_fahrenheit(self):
        fetcher = fetcher_for({"http://weather.example.com/harlow": FakeResponse(fixture("weather.html"))})
        out = io.StringIO()
        cli.main(["weather", "http://weather.example.com/harlow", "--fahrenheit"], fetcher, out)
        self.assertIn("57F", out.getvalue())


if __name__ == "__main__":
    unittest.main()
