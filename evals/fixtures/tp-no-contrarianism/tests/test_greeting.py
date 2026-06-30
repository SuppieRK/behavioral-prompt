import unittest

from src.greeting import greeting


class GreetingTest(unittest.TestCase):
    def test_greeting_has_period(self):
        self.assertEqual(greeting("Ada"), "Hello, Ada.")
