def final_price(base_cents, discount_percent, tax_percent):
    if discount_percent < 0:
        raise ValueError("discount cannot be negative")
    if tax_percent < 0:
        raise ValueError("tax cannot be negative")
    return round((base_cents - (base_cents * discount_percent / 100)) * (1 + tax_percent / 100))
