from datetime import date


class RenewalNotice:
    def __init__(self, today_provider):
        self._today_provider = today_provider

    def message(self, renewal_date: date) -> str:
        return f"Renews on {renewal_date:%B %-d, %Y}"
