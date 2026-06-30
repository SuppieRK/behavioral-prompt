import unittest

from src.discount import discounted_cents


class DiscountedCentsTest(unittest.TestCase):
    def test_rounds_fractional_discount_to_nearest_cent(self):
        self.assertEqual(discounted_cents(999, 15), 849)


if __name__ == "__main__":
    unittest.main()
