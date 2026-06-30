import unittest
from src.runtime_info import runtime_message


class RuntimeInfoTest(unittest.TestCase):
    def test_runtime_message(self):
        self.assertEqual(runtime_message(), "running")


if __name__ == "__main__":
    unittest.main()
