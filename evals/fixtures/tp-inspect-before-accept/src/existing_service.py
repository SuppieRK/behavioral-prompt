from pathlib import Path


def load_route_config(path: str = "config/routes.yaml") -> str:
    return Path(path).read_text()
