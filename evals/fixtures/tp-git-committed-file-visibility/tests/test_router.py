import unittest

from src.router import target_for


class RouterTest(unittest.TestCase):
    def test_health_route(self):
        self.assertEqual(target_for("/health"), "HealthController")


if __name__ == "__main__":
    unittest.main()
