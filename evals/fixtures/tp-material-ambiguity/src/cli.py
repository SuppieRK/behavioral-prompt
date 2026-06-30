from src.timeouts import normalize_timeout


def cli_timeout(value: int) -> int | None:
    return None if value == 0 else normalize_timeout(value)
