import unittest

from src.api import customer_payload


class CustomerApiTest(unittest.TestCase):
    def test_customer_name_is_normalized(self):
        self.assertEqual(customer_payload(" ADA "), {"name": "ada"})


if __name__ == "__main__":
    unittest.main()
