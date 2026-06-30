from src.names import normalize_name


def customer_payload(name: str) -> dict[str, str]:
    return {"name": normalize_name(name)}
