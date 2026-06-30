import unittest
from src.message import welcome


class MessageTest(unittest.TestCase):
    def test_welcome(self):
        self.assertEqual(welcome("Ada"), "Welcome Ada")


if __name__ == "__main__":
    unittest.main()
