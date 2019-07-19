import os
import unittest

from datetime import datetime, timezone

from py_scrapers.rss import newest_first, parse_rfc822, parse_rss


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

    def test_missing_date_is_none(self):
        self.assertIsNone(parse_rss(fixture("feed.xml"))[3]["published"])

    def test_dates_are_converted_to_utc(self):
        items = parse_rss(fixture("feed.xml"))
        self.assertEqual(items[0]["published"], datetime(2019, 7, 2, 9, 30, tzinfo=timezone.utc))
        self.assertEqual(items[1]["published"], datetime(2019, 6, 28, 13, 5, tzinfo=timezone.utc))

    def test_bad_dates(self):
        self.assertIsNone(parse_rfc822("last tuesday"))
        self.assertIsNone(parse_rfc822(""))

    def test_newest_first(self):
        titles = [i["title"] for i in newest_first(parse_rss(fixture("feed.xml")))]
        self.assertEqual(titles, ["Market stalls return to the square", "Council approves new cycle lane",
                                  "Library extends opening hours", "Letters page"])


if __name__ == "__main__":
    unittest.main()
