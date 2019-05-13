import unittest
from decimal import Decimal

from py_scrapers.books import parse_price


class ParsePriceTests(unittest.TestCase):
    def test_pounds(self):
        self.assertEqual(parse_price("£51.77"), Decimal("51.77"))

    def test_other_symbols_and_spaces(self):
        self.assertEqual(parse_price(" $9.99 "), Decimal("9.99"))
        self.assertEqual(parse_price("€10"), Decimal("10"))

    def test_garbage(self):
        with self.assertRaises(ValueError):
            parse_price("free!")


if __name__ == "__main__":
    unittest.main()
