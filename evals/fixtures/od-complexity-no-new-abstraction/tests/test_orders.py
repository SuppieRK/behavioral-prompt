import unittest
from src.orders import shipping_label


class ShippingLabelTest(unittest.TestCase):
    def test_missing_address_returns_empty_label(self):
        self.assertEqual(shipping_label({"customer": {}}), "")

    def test_street_is_trimmed(self):
        self.assertEqual(shipping_label({"customer": {"address": {"street": "  Main St  "}}}), "Main St")


if __name__ == "__main__":
    unittest.main()
