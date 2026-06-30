from decimal import Decimal


def discounted_cents(total_cents: int, percent: int) -> int:
    discount = Decimal(total_cents) * Decimal(percent) / Decimal(100)
    return total_cents - int(discount)
