from src.parser import parse_price


def total(raw_prices):
    return sum(parse_price(value) for value in raw_prices)
