import unittest

from src.receipt import format_total


class ReceiptTest(unittest.TestCase):
    def test_total_uses_two_decimal_places(self):
        self.assertEqual(format_total(1250), "$12.50")


if __name__ == "__main__":
    unittest.main()
