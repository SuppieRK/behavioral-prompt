import unittest
from src.discounts import discount_percent


class DiscountTest(unittest.TestCase):
    def test_premium_discount(self):
        self.assertEqual(discount_percent("premium"), 20)


if __name__ == "__main__":
    unittest.main()
