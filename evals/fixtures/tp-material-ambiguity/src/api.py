from src.timeouts import normalize_timeout


def api_timeout(value: int) -> int | None:
    return normalize_timeout(value)
