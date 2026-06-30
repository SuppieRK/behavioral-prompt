import unittest
from src.shipping import shipping_cost


class ShippingTest(unittest.TestCase):
    def test_shipping_under_threshold(self):
        self.assertEqual(shipping_cost(40), 5)


if __name__ == "__main__":
    unittest.main()
