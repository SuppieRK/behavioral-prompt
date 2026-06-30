import unittest
from src.invoice import format_total


class FormatTotalTest(unittest.TestCase):
    def test_format_total_includes_label(self):
        self.assertEqual(format_total(12.5), "Total: $12.50")


if __name__ == "__main__":
    unittest.main()
