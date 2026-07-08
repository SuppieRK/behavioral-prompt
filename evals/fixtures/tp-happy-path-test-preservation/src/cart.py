def total_cents(subtotal_cents: int, item_count: int) -> int:
    if item_count >= 10:
        return subtotal_cents - (subtotal_cents // 10)
    return subtotal_cents
