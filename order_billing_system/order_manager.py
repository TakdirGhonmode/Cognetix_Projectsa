from database import Database
from datetime import date
from validation import *

db = Database()


class OrderManager:

    # ---------------------------------
    # Create Order
    # ---------------------------------
    def create_order(self):

        print("\n========== CREATE ORDER ==========")

        while True:
            customer_name = input("Enter Customer Name : ")
            if validate_name(customer_name):
                break

        while True:
            customer_phone = input("Enter Phone Number : ")
            if validate_phone(customer_phone):
                break

        while True:
            customer_email = input("Enter Email : ")
            if validate_email(customer_email):
                break

        query = """
        INSERT INTO orders
        (
            customer_name,
            customer_phone,
            customer_email,
            order_date,
            status,
            subtotal,
            tax,
            total_amount
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """

        values = (
            customer_name,
            customer_phone,
            customer_email,
            date.today(),
            "Created",
            0,
            0,
            0
        )

        db.cursor.execute(query, values)
        db.connection.commit()

        order_id = db.cursor.lastrowid

        print("\nOrder Created Successfully.")
        print("Order ID :", order_id)

        self.add_products(order_id)

    # ---------------------------------
    # Add Products
    # ---------------------------------
    def add_products(self, order_id):

        subtotal = 0

        while True:

            print("\n========== ADD PRODUCT ==========")

            while True:
                product = input("Product Name : ").strip()

                if product:
                    break

                print("Product name cannot be empty.")

            while True:
                quantity = input("Quantity : ")

                if validate_quantity(quantity):
                    quantity = int(quantity)
                    break

            while True:
                price = input("Price : ")

                if validate_price(price):
                    price = float(price)
                    break

            total_price = quantity * price
            subtotal += total_price

            query = """
            INSERT INTO order_items
            (
                order_id,
                product_name,
                quantity,
                price,
                total_price
            )
            VALUES (%s,%s,%s,%s,%s)
            """

            values = (
                order_id,
                product,
                quantity,
                price,
                total_price
            )

            db.cursor.execute(query, values)
            db.connection.commit()

            choice = input("\nAdd Another Product? (y/n): ").lower()

            if choice != "y":
                break

        # Billing Calculation
        tax = round(subtotal * 0.18, 2)
        final_amount = round(subtotal + tax, 2)

        update_query = """
        UPDATE orders
        SET
            subtotal=%s,
            tax=%s,
            total_amount=%s
        WHERE order_id=%s
        """

        db.cursor.execute(
            update_query,
            (
                subtotal,
                tax,
                final_amount,
                order_id
            )
        )

        db.connection.commit()

        print("\n========== BILL SUMMARY ==========")
        print(f"Subtotal      : ₹{subtotal:.2f}")
        print(f"Tax (18%)     : ₹{tax:.2f}")
        print(f"Final Amount  : ₹{final_amount:.2f}")

        print("\nProducts Added Successfully.")
    def view_orders(self):

     query = "SELECT * FROM orders"

     db.cursor.execute(query)

     orders = db.cursor.fetchall()

     if not orders:
         print("\nNo Orders Found.")
         return

     print("\n========== ALL ORDERS ==========")

     for order in orders:
         print(f"""
Order ID        : {order[0]}
Customer Name   : {order[1]}
Phone           : {order[2]}
Email           : {order[3]}
Order Date      : {order[4]}
Status          : {order[5]}
Subtotal        : ₹{order[6]}
Tax             : ₹{order[7]}
Total Amount    : ₹{order[8]}
---------------------------------------
""")   
    def search_order(self):

     order_id = int(input("Enter Order ID : "))

     query = "SELECT * FROM orders WHERE order_id=%s"

     db.cursor.execute(query, (order_id,))

     order = db.cursor.fetchone()

     if order:

         print("\n========== ORDER DETAILS ==========")

         print(f"""
Order ID      : {order[0]}
Customer      : {order[1]}
Phone         : {order[2]}
Email         : {order[3]}
Date          : {order[4]}
Status        : {order[5]}
Subtotal      : ₹{order[6]}
Tax           : ₹{order[7]}
Total Amount  : ₹{order[8]}
""")

         db.cursor.execute(
             "SELECT product_name,quantity,price,total_price FROM  order_items WHERE order_id=%s",
             (order_id,)
         )

         items = db.cursor.fetchall()

         print("Products")

         for item in items:
             print(
                 f"{item[0]} | Qty:{item[1]} | Price:{item[2]} | Total: {item[3]}"
             )

     else:
         print("Order Not Found.")
    def update_order_status(self):

     order_id = int(input("Enter Order ID : "))

     status = input(
         "Enter Status (Created/Confirmed/Shipped/Delivered/Cancelled): "
     )

     if not validate_order_status(status):
         return

     query = """
     UPDATE orders
     SET status=%s
     WHERE order_id=%s
     """

     db.cursor.execute(query, (status, order_id))

     db.connection.commit()

     print("Status Updated Successfully.")
     
    def delete_order(self):

     order_id = int(input("Enter Order ID : "))

     query = "DELETE FROM orders WHERE order_id=%s"

     db.cursor.execute(query, (order_id,))

     db.connection.commit()

     print("Order Deleted Successfully.")
    