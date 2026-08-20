from database import Database

db = Database()


class Reports:

    def transaction_history(self):

        db.cursor.execute("""
            SELECT
            t.transaction_id,
            t.order_id,
            p.payment_method,
            t.amount,
            t.transaction_date
            FROM transactions t
            JOIN payments p
            ON t.payment_id=p.payment_id
        """)

        rows = db.cursor.fetchall()

        print("\n========== TRANSACTION HISTORY ==========")

        for row in rows:

            print(f"""
Transaction ID : {row[0]}
Order ID       : {row[1]}
Method         : {row[2]}
Amount         : ₹{row[3]}
Date           : {row[4]}
-----------------------------------------
""")
    def summary_report(self):

     db.cursor.execute("SELECT COUNT(*) FROM orders")
     total_orders = db.cursor.fetchone()[0]

     db.cursor.execute("SELECT COUNT(*) FROM invoices")
     total_invoices = db.cursor.fetchone()[0]

     db.cursor.execute("SELECT COUNT(*) FROM payments")
     total_payments = db.cursor.fetchone()[0]

     db.cursor.execute("SELECT SUM(payment_amount) FROM payments")
     revenue = db.cursor.fetchone()[0]

     if revenue is None:
         revenue = 0

     print("\n========== SUMMARY REPORT ==========")

     print(f"Total Orders     : {total_orders}")
     print(f"Total Invoices   : {total_invoices}")
     print(f"Total Payments   : {total_payments}")
     print(f"Total Revenue    : ₹{revenue}")