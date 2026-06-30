import unittest

from src.export import customer_row


class CustomerExportTest(unittest.TestCase):
    def test_export_name_remains_lowercase(self):
        self.assertEqual(customer_row(" ADA "), "ada")


if __name__ == "__main__":
    unittest.main()
