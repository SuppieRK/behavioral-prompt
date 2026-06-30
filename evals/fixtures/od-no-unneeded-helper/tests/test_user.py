import unittest
from src.user import display_name


class DisplayNameTest(unittest.TestCase):
    def test_display_name(self):
        self.assertEqual(display_name("Ada", "Lovelace"), "Ada Lovelace")


if __name__ == "__main__":
    unittest.main()
