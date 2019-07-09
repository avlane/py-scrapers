import os
import unittest

from py_scrapers.weather import forecast_days, format_days, parse_forecast, parse_number, to_fahrenheit

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


class NumberTests(unittest.TestCase):
    def test_numbers(self):
        self.assertEqual(parse_number("14°C"), 14)
        self.assertEqual(parse_number("-1°C"), -1)
        self.assertEqual(parse_number("80%"), 80)
        self.assertEqual(parse_number("5.8 m"), 5.8)

    def test_missing_values(self):
        self.assertIsNone(parse_number("—"))
        self.assertIsNone(parse_number(""))


class DaysTests(unittest.TestCase):
    def test_days(self):
        days = forecast_days(PAGE)
        self.assertEqual(days[0].high, 14)
        self.assertEqual(days[3].rain_chance, None)
        self.assertEqual(days[4].low, -1)


class FormatTests(unittest.TestCase):
    def test_celsius_table(self):
        lines = format_days(forecast_days(PAGE)).splitlines()
        self.assertEqual(len(lines), 6)
        self.assertTrue(lines[1].startswith("Mon 3 Jun"))
        self.assertIn("14C", lines[1])
        self.assertTrue(lines[4].rstrip().endswith("-"))

    def test_fahrenheit(self):
        self.assertEqual(to_fahrenheit(0), 32)
        self.assertEqual(to_fahrenheit(None), None)
        self.assertIn("57F", format_days(forecast_days(PAGE), fahrenheit=True).splitlines()[1])


if __name__ == "__main__":
    unittest.main()
