import mysql.connector
from config import HOST, USER, PASSWORD, DATABASE


class Database:

    def __init__(self):
        self.connection = mysql.connector.connect(
            host=HOST,
            user=USER,
            password=PASSWORD
        )

        self.cursor = self.connection.cursor()

        self.create_database()

        self.connection.database = DATABASE

        self.create_tables()

    # -------------------------
    # Create Database
    # -------------------------

    def create_database(self):

        self.cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {DATABASE}"
        )

    # -------------------------
    # Create Tables
    # -------------------------

    def create_tables(self):

        # Orders Table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders(

            order_id INT AUTO_INCREMENT PRIMARY KEY,

            customer_name VARCHAR(100) NOT NULL,

            customer_phone VARCHAR(15) NOT NULL,

            customer_email VARCHAR(100),

            order_date DATE NOT NULL,

            status ENUM(
            'Created',
            'Confirmed',
            'Shipped',
            'Delivered',
            'Cancelled'
            ) DEFAULT 'Created',

            subtotal DECIMAL(10,2),

            tax DECIMAL(10,2),

            total_amount DECIMAL(10,2)

        )
        """)

        # Order Items Table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items(

            item_id INT AUTO_INCREMENT PRIMARY KEY,

            order_id INT,

            product_name VARCHAR(100),

            quantity INT,

            price DECIMAL(10,2),

            total_price DECIMAL(10,2),

            FOREIGN KEY(order_id)
            REFERENCES orders(order_id)
            ON DELETE CASCADE

        )
        """)

        # Invoice Table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices(

            invoice_id INT AUTO_INCREMENT PRIMARY KEY,

            order_id INT UNIQUE,

            invoice_date DATE,

            subtotal DECIMAL(10,2),

            tax DECIMAL(10,2),

            total_amount DECIMAL(10,2),

            FOREIGN KEY(order_id)
            REFERENCES orders(order_id)
            ON DELETE CASCADE

        )
        """)

        # Payment Table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments(

            payment_id INT AUTO_INCREMENT PRIMARY KEY,

            order_id INT,

            payment_amount DECIMAL(10,2),

            payment_method ENUM(
            'Cash',
            'UPI',
            'Card',
            'Net Banking'
            ),

            payment_status ENUM(
            'Pending',
            'Paid',
            'Partially Paid'
            ) DEFAULT 'Pending',

            payment_date DATE,

            FOREIGN KEY(order_id)
            REFERENCES orders(order_id)
            ON DELETE CASCADE

        )
        """)

        # Transaction Table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions(

            transaction_id INT AUTO_INCREMENT PRIMARY KEY,

            payment_id INT,

            order_id INT,

            amount DECIMAL(10,2),

            transaction_date DATE,

            FOREIGN KEY(payment_id)
            REFERENCES payments(payment_id)
            ON DELETE CASCADE,

            FOREIGN KEY(order_id)
            REFERENCES orders(order_id)
            ON DELETE CASCADE

        )
        """)

        self.connection.commit()

        print("Database & Tables Created Successfully")


db = Database()