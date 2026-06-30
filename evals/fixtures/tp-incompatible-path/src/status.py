def status_label(code: int) -> str:
    if code == 200:
        return "ok"
    if code == 404:
        return "missing"
    return "unknown"
