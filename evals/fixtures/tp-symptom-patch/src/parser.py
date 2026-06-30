def parse_price(raw):
    # BUG: empty strings should be treated as missing prices, not parsed.
    return float(raw)
