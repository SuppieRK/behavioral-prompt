import unittest

from src.render import render_name


class RenderNameTest(unittest.TestCase):
    def test_plain_name(self):
        self.assertEqual(render_name("Ada"), "<span>Ada</span>")


if __name__ == "__main__":
    unittest.main()
