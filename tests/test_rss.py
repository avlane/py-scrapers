import os
import unittest

from datetime import datetime, timezone

from py_scrapers.rss import newest_first, parse_iso8601, parse_rfc822, parse_rss, since


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


class SinceTests(unittest.TestCase):
    def test_since_drops_older_and_undated_items(self):
        items = parse_rss(fixture("feed.xml"))
        recent = since(items, datetime(2019, 7, 1, tzinfo=timezone.utc))
        self.assertEqual(sorted(i["title"] for i in recent),
                         ["Council approves new cycle lane", "Market stalls return to the square"])


class AtomTests(unittest.TestCase):
    def test_entries(self):
        items = parse_rss(fixture("atom.xml"))
        self.assertEqual([i["title"] for i in items], ["Tide tables for July", "Harbour wall repairs"])
        self.assertEqual(items[0]["link"], "https://notes.example.org/tides-july")
        self.assertEqual(items[1]["link"], "https://notes.example.org/harbour-wall")

    def test_prefers_published_over_updated(self):
        items = parse_rss(fixture("atom.xml"))
        self.assertEqual(items[1]["published"], datetime(2019, 7, 4, 17, 45, tzinfo=timezone.utc))

    def test_content_is_used_when_there_is_no_summary(self):
        self.assertEqual(parse_rss(fixture("atom.xml"))[1]["summary"], "Repairs begin next week.")

    def test_iso8601_offsets(self):
        self.assertEqual(parse_iso8601("2019-07-04T18:45:00+01:00"), datetime(2019, 7, 4, 17, 45, tzinfo=timezone.utc))
        self.assertIsNone(parse_iso8601("yesterday"))


if __name__ == "__main__":
    unittest.main()
