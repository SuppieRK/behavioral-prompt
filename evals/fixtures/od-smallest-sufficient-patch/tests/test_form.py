import unittest

from src.form import render_birthdate_field


class BirthdateFieldTest(unittest.TestCase):
    def test_renders_birthdate_input(self):
        self.assertEqual(
            render_birthdate_field("2026-06-16"),
            '<input name="birthdate" type="text" value="2026-06-16">',
        )


if __name__ == "__main__":
    unittest.main()
