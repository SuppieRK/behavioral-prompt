import unittest

from src.orders import create_order, update_order


class OrdersTest(unittest.TestCase):
    def test_existing_paths_normalize_names(self):
        self.assertEqual(create_order(" A "), {"name": "a"})
        self.assertEqual(update_order(" B "), {"name": "b"})
