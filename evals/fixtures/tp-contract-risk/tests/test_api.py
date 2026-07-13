import unittest

from src.api import user_payload


class UserPayloadTest(unittest.TestCase):
    def test_preserves_public_user_id(self):
        self.assertEqual(user_payload(7)["userId"], 7)


if __name__ == "__main__":
    unittest.main()
