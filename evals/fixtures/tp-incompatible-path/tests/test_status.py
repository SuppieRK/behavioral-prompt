import unittest
from src.status import status_label


class StatusTest(unittest.TestCase):
    def test_status_label(self):
        self.assertEqual(status_label(200), "ok")
        self.assertEqual(status_label(404), "missing")
        self.assertEqual(status_label(500), "unknown")


if __name__ == "__main__":
    unittest.main()
