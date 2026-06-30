import unittest

from src.discount import discounted_total


class DiscountTest(unittest.TestCase):
    def test_twenty_percent_discount(self):
        self.assertEqual(discounted_total(100, 20), 80)


if __name__ == "__main__":
    unittest.main()
