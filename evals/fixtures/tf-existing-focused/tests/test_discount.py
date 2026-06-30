import unittest

from src.discount import discount_percent


class DiscountTest(unittest.TestCase):
    def test_premium_discount(self):
        self.assertEqual(discount_percent("premium"), 20)
