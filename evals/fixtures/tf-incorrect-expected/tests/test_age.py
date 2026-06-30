import unittest
from src.age import is_adult


class AgeTest(unittest.TestCase):
    def test_eighteen_is_adult(self):
        self.assertTrue(is_adult(18))


if __name__ == "__main__":
    unittest.main()
