from database import Database
from datetime import date

db = Database()


class Billing:

    def generate_invoice(self):

        order_id = int(input("Enter Order ID : "))

        # Check if invoice already exists
        db.cursor.execute(
            "SELECT * FROM invoices WHERE order_id=%s",
            (order_id,)
        )

        if db.cursor.fetchone():
            print("Invoice already exists.")
            return

        # Fetch order
        db.cursor.execute(
            "SELECT subtotal,tax,total_amount,status FROM orders WHERE order_id=%s",
            (order_id,)
        )

        order = db.cursor.fetchone()

        if not order:
            print("Order Not Found.")
            return

        subtotal, tax, total, status = order

        if status == "Cancelled":
            print("Cannot generate invoice for cancelled order.")
            return

        db.cursor.execute("""
            INSERT INTO invoices
            (order_id,invoice_date,subtotal,tax,total_amount)
            VALUES(%s,%s,%s,%s,%s)
        """, (
            order_id,
            date.today(),
            subtotal,
            tax,
            total
        ))

        db.connection.commit()

        print("\n===== INVOICE GENERATED =====")
        print(f"Order ID : {order_id}")
        print(f"Subtotal : ₹{subtotal}")
        print(f"Tax      : ₹{tax}")
        print(f"Total    : ₹{total}")
    def view_invoice(self):

     order_id = int(input("Enter Order ID : "))

     db.cursor.execute("""
     SELECT *
     FROM invoices
     WHERE order_id=%s
     """, (order_id,))

     invoice = db.cursor.fetchone()

     if not invoice:
         print("Invoice Not Found.")
         return

     print("\n========== INVOICE ==========")

     print(f"Invoice ID   : {invoice[0]}")
     print(f"Order ID     : {invoice[1]}")
     print(f"Invoice Date : {invoice[2]}")
     print(f"Subtotal     : ₹{invoice[3]}")
     print(f"Tax          : ₹{invoice[4]}")
     print(f"Total Amount : ₹{invoice[5]}")