import unittest
from datetime import date

from src.renewal_notice import RenewalNotice


FIXED_TODAY = date(2026, 2, 3)


class RenewalNoticeTest(unittest.TestCase):
    def test_future_renewal_shows_date(self):
        notice = RenewalNotice(lambda: FIXED_TODAY)

        self.assertEqual("Renews on February 10, 2026", notice.message(date(2026, 2, 10)))


if __name__ == "__main__":
    unittest.main()
