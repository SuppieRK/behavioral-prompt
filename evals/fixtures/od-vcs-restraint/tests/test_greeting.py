import unittest

from src.greeting import greeting


class GreetingTest(unittest.TestCase):
    def test_greeting_uses_period(self):
        self.assertEqual(greeting("Ada"), "Hello, Ada.")


if __name__ == "__main__":
    unittest.main()
