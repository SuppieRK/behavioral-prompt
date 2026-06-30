import unittest
from src.banner import banner_text


class BannerTest(unittest.TestCase):
    def test_banner_text(self):
        self.assertEqual(banner_text("Ada"), "Welcome, Ada!")


if __name__ == "__main__":
    unittest.main()
