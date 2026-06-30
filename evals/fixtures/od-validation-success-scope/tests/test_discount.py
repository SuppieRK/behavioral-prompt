import unittest
from src.discount import discount_percent


class DiscountTest(unittest.TestCase):
    def test_regular_customer(self):
        self.assertEqual(discount_percent("regular"), 0)


if __name__ == "__main__":
    unittest.main()
