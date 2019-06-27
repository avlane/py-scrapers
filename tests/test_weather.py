import os
import unittest

from py_scrapers.weather import parse_forecast

with open(os.path.join(os.path.dirname(__file__), "fixtures", "weather.html"), encoding="utf-8") as _f:
    PAGE = _f.read()


class ForecastTests(unittest.TestCase):
    def test_rows(self):
        rows = parse_forecast(PAGE)
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0], {"day": "Mon 3 Jun", "outlook": "Light rain", "high": "14°C",
                                   "low": "9°C", "rain": "80%"})

    def test_picks_the_requested_table(self):
        rows = parse_forecast(PAGE, table_id="tides")
        self.assertEqual(rows, [{"time": "04:12", "height": "5.8 m"}])

    def test_missing_table(self):
        with self.assertRaises(ValueError):
            parse_forecast("<p>nothing</p>")


if __name__ == "__main__":
    unittest.main()
