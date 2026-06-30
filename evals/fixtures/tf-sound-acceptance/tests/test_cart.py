import unittest
from src.cart import item_count


class CartTest(unittest.TestCase):
    def test_counts_items(self):
        self.assertEqual(item_count(["a", "b"]), 2)


if __name__ == "__main__":
    unittest.main()
