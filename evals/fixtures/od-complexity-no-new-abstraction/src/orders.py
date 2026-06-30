def shipping_label(order):
    label = ""
    if order is not None:
        customer = order.get("customer")
        if customer is not None:
            address = customer.get("address")
            if address is not None:
                street = address.get("street")
                if street:
                    label = street.strip()
    return label
