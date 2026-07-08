import unittest

from src.payload_template import default_payload


class DefaultPayloadTest(unittest.TestCase):
    def test_default_payload(self):
        self.assertEqual("pending", default_payload())


if __name__ == "__main__":
    unittest.main()
