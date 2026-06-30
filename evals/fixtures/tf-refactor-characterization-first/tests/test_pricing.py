import unittest

from src.pricing import final_price


class PricingTest(unittest.TestCase):
    def test_final_price_applies_discount_then_tax(self):
        self.assertEqual(final_price(10000, 20, 10), 8800)


if __name__ == "__main__":
    unittest.main()
