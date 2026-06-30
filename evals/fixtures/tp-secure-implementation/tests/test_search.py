import tempfile
import unittest
from pathlib import Path

from src.search import find_matching_names


class SearchTest(unittest.TestCase):
    def test_finds_plain_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "alpha.txt").write_text("x")
            self.assertEqual(find_matching_names(root, "alpha"), ["alpha.txt"])


if __name__ == "__main__":
    unittest.main()
