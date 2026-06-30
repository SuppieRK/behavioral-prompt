import unittest
from src.string_utils import slugify


class SlugifyTest(unittest.TestCase):
    def test_replaces_spaces(self):
        self.assertEqual(slugify("Hello World"), "hello-world")


if __name__ == "__main__":
    unittest.main()
