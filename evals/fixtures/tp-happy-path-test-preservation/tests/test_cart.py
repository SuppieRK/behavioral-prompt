import unittest

from src.cart import total_cents


class TotalCentsTest(unittest.TestCase):
    def test_standard_order_keeps_subtotal(self):
        self.assertEqual(2500, total_cents(2500, 3))

    def test_bulk_order_gets_discount(self):
        self.assertEqual(9000, total_cents(10000, 10))


if __name__ == "__main__":
    unittest.main()
