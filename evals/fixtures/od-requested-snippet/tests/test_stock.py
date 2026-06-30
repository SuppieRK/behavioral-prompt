import unittest

from src.stock import stock_label


class StockTest(unittest.TestCase):
    def test_count_below_ten_is_low(self):
        self.assertEqual(stock_label(5), "low")


if __name__ == "__main__":
    unittest.main()
