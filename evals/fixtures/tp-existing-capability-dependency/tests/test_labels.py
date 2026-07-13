import unittest

from src.labels import label_for


class LabelForTest(unittest.TestCase):
    def test_uses_existing_slug_helper(self):
        self.assertEqual("launch-plan", label_for(" Launch Plan "))


if __name__ == "__main__":
    unittest.main()
