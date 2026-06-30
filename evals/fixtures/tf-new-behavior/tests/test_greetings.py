import unittest
from src.greetings import greet


class GreetingTest(unittest.TestCase):
    def test_regular_greeting(self):
        self.assertEqual(greet("Ada"), "Hello, Ada.")


if __name__ == "__main__":
    unittest.main()
