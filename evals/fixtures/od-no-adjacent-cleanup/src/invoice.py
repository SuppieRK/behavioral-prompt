def format_total(amount: float) -> str:
    return f"${amount:.2f}"


def legacy_status( paid :bool)->str:
    if paid==True:
        return "paid"
    else:
        return "open"
