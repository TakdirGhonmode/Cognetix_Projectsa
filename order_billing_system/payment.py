from database import Database
from validation import *
from datetime import date

db = Database()


class Payment:

    def record_payment(self):

        order_id = int(input("Enter Order ID : "))

        db.cursor.execute(
            "SELECT total_amount FROM orders WHERE order_id=%s",
            (order_id,)
        )

        order = db.cursor.fetchone()

        if not order:
            print("Order Not Found.")
            return

        total = float(order[0])

        while True:
            amount = input("Enter Payment Amount : ")

            if validate_payment_amount(amount):
                amount = float(amount)
                break

        while True:
            method = input("Payment Method (Cash/UPI/Card/Net Banking): ")

            if validate_payment_method(method):
                break

        status = "Paid" if amount >= total else "Partially Paid"

        db.cursor.execute("""
            INSERT INTO payments
            (order_id,payment_amount,payment_method,payment_status,payment_date)
            VALUES(%s,%s,%s,%s,%s)
        """, (
            order_id,
            amount,
            method,
            status,
            date.today()
        ))

        payment_id = db.cursor.lastrowid

        db.cursor.execute("""
            INSERT INTO transactions
            (payment_id,order_id,amount,transaction_date)
            VALUES(%s,%s,%s,%s)
        """, (
            payment_id,
            order_id,
            amount,
            date.today()
        ))

        db.connection.commit()

        print("Payment Recorded Successfully.")
    def view_payments(self):

     db.cursor.execute("SELECT * FROM payments")

     payments = db.cursor.fetchall()

     print("\n========== PAYMENTS ==========")

     for payment in payments:

         print(f"""
Payment ID      : {payment[0]}
Order ID        : {payment[1]}
Amount          : ₹{payment[2]}
Method          : {payment[3]}
Status          : {payment[4]}
Payment Date    : {payment[5]}
---------------------------------------
""")