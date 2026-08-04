import re


def validate_name(name):
    if not name.strip():
        print("Customer name cannot be empty.")
        return False
    return True


def validate_phone(phone):
    if not phone.isdigit():
        print("Phone number must contain only digits.")
        return False

    if len(phone) != 10:
        print("Phone number must contain exactly 10 digits.")
        return False

    return True


def validate_email(email):
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

    if re.fullmatch(pattern, email):
        return True

    print("Invalid email address. Example: abc@gmail.com")
    return False


def validate_quantity(quantity):
    try:
        quantity = int(quantity)

        if quantity > 0:
            return True

        print("Quantity must be greater than 0.")
        return False

    except ValueError:
        print("Quantity must be a number.")
        return False


def validate_price(price):
    try:
        price = float(price)

        if price > 0:
            return True

        print("Price must be greater than 0.")
        return False

    except ValueError:
        print("Price must be a valid number.")
        return False


def validate_tax(tax):
    try:
        tax = float(tax)

        if tax >= 0:
            return True

        print("Tax cannot be negative.")
        return False

    except ValueError:
        print("Tax must be a valid number.")
        return False


def validate_payment_amount(amount):
    try:
        amount = float(amount)

        if amount > 0:
            return True

        print("Payment amount must be greater than 0.")
        return False

    except ValueError:
        print("Payment amount must be a valid number.")
        return False


def validate_order_status(status):
    valid_status = [
        "Created",
        "Confirmed",
        "Shipped",
        "Delivered",
        "Cancelled"
    ]

    if status in valid_status:
        return True

    print("Invalid order status.")
    return False


def validate_payment_method(method):
    valid_methods = [
        "Cash",
        "UPI",
        "Card",
        "Net Banking"
    ]

    if method in valid_methods:
        return True

    print("Invalid payment method.")
    return False