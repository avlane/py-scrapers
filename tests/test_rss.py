import os
import unittest

from py_scrapers.rss import parse_rss


def fixture(name):
    with open(os.path.join(os.path.dirname(__file__), "fixtures", name), encoding="utf-8") as f:
        return f.read()


class RssTests(unittest.TestCase):
    def test_items(self):
        items = parse_rss(fixture("feed.xml"))
        self.assertEqual(len(items), 4)
        self.assertEqual(items[0]["title"], "Council approves new cycle lane")
        self.assertEqual(items[0]["link"], "https://gazette.example.com/news/cycle-lane")

    def test_cdata_summary(self):
        items = parse_rss(fixture("feed.xml"))
        self.assertIn("<b>Hill Street</b>", items[0]["summary"])

    def test_missing_date_is_empty(self):
        self.assertEqual(parse_rss(fixture("feed.xml"))[3]["published"], "")


if __name__ == "__main__":
    unittest.main()
