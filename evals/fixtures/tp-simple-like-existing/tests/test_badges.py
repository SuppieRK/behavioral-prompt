import unittest

from src.badges import project_badge, user_badge


class BadgeTest(unittest.TestCase):
    def test_user_badge(self):
        self.assertEqual("[Ada]", user_badge(" Ada "))

    def test_project_badge(self):
        self.assertEqual("Launch", project_badge("Launch"))


if __name__ == "__main__":
    unittest.main()
