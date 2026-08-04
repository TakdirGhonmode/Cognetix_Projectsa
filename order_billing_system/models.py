class Customer:
    def __init__(self, name, phone, email):
        self.name = name
        self.phone = phone
        self.email = email


class Order:
    def __init__(self, customer_name, customer_phone, customer_email,
                 order_date, status="Created",
                 subtotal=0.0, tax=0.0, total_amount=0.0):

        self.customer_name = customer_name
        self.customer_phone = customer_phone
        self.customer_email = customer_email
        self.order_date = order_date
        self.status = status
        self.subtotal = subtotal
        self.tax = tax
        self.total_amount = total_amount


class OrderItem:
    def __init__(self, order_id, product_name, quantity, price):

        self.order_id = order_id
        self.product_name = product_name
        self.quantity = quantity
        self.price = price
        self.total_price = quantity * price


class Invoice:
    def __init__(self, order_id, invoice_date,
                 subtotal, tax, total_amount):

        self.order_id = order_id
        self.invoice_date = invoice_date
        self.subtotal = subtotal
        self.tax = tax
        self.total_amount = total_amount


class Payment:
    def __init__(self, order_id, payment_amount,
                 payment_method,
                 payment_status="Pending",
                 payment_date=None):

        self.order_id = order_id
        self.payment_amount = payment_amount
        self.payment_method = payment_method
        self.payment_status = payment_status
        self.payment_date = payment_date


class Transaction:
    def __init__(self, payment_id, order_id,
                 amount, transaction_date):

        self.payment_id = payment_id
        self.order_id = order_id
        self.amount = amount
        self.transaction_date = transaction_date