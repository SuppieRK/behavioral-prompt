import unittest
from src.tax import calculate_tax


class TaxTest(unittest.TestCase):
    def test_tax_is_ten_percent(self):
        self.assertEqual(calculate_tax(100), 10)


if __name__ == "__main__":
    unittest.main()
