import unittest

from src.labels import label


class LabelTest(unittest.TestCase):
    def test_existing_behavior(self):
        self.assertEqual(label(" value "), "value")
