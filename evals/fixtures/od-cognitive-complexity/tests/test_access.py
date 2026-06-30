import unittest
from src.access import can_access


class AccessTest(unittest.TestCase):
    def test_admin_can_access(self):
        self.assertTrue(can_access({"active": True, "locked": False, "roles": ["admin"]}))

    def test_verified_editor_can_access(self):
        self.assertTrue(can_access({"active": True, "locked": False, "roles": ["editor"], "verified": True}))

    def test_locked_user_cannot_access(self):
        self.assertFalse(can_access({"active": True, "locked": True, "roles": ["admin"]}))


if __name__ == "__main__":
    unittest.main()
