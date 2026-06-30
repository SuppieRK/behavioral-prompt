import unittest

from src.checkout import checkout_total


class CheckoutTotalTest(unittest.TestCase):
    def test_no_fee_at_fifty(self):
        self.assertEqual(checkout_total(50), 50)


if __name__ == "__main__":
    unittest.main()
