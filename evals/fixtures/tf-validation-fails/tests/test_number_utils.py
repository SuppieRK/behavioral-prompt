import unittest
from src.number_utils import parse_int_or_zero


class ParseIntOrZeroTest(unittest.TestCase):
    def test_valid_integer(self):
        self.assertEqual(parse_int_or_zero("42"), 42)

    def test_invalid_integer_returns_zero(self):
        self.assertEqual(parse_int_or_zero("abc"), 0)


if __name__ == "__main__":
    unittest.main()
