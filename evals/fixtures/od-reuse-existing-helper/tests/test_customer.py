import unittest

from src.customer import customer_slug


class CustomerTest(unittest.TestCase):
    def test_customer_slug_uses_hyphens(self):
        self.assertEqual(customer_slug(" Ada Lovelace "), "ada-lovelace")
