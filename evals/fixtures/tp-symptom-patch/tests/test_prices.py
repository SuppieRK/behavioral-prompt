import unittest

from src.parser import parse_price


class PriceTest(unittest.TestCase):
    def test_empty_price_is_missing(self):
        self.assertIsNone(parse_price(""))

    def test_invalid_nonempty_price_still_fails(self):
        with self.assertRaises(ValueError):
            parse_price("invalid")
