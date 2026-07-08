import unittest

from src.app import greeting


class GreetingTest(unittest.TestCase):
    def test_greeting(self):
        self.assertEqual(greeting(), "Hello, eval harness!")


if __name__ == "__main__":
    unittest.main()
