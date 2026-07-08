import unittest

from src.greeting import format_customer_name


class FormatCustomerNameTest(unittest.TestCase):
    def test_formats_customer_name(self):
        self.assertEqual("Hello, Ada!", format_customer_name("Ada"))


if __name__ == "__main__":
    unittest.main()
