from pathlib import Path


ROUTES_PATH = Path(".service/routes.txt")


def target_for(path: str) -> str | None:
    for line in ROUTES_PATH.read_text().splitlines():
        route, target = line.split("=", 1)
        if route == path:
            return target
    return None
