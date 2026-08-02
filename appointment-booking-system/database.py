import mysql.connector


class Database:

    def __init__(self):
        self.connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Takdir@1234",
            database="appointment_booking_system"
        )

        self.cursor = self.connection.cursor()

        # Automatically create tables
        self.create_tables()

    # ---------------------------------
    # Create Tables
    # ---------------------------------

    def create_tables(self):

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS slots(
            slot_id INT AUTO_INCREMENT PRIMARY KEY,
            service_type VARCHAR(100),
            date DATE,
            start_time TIME,
            end_time TIME,
            duration INT,
            status VARCHAR(20)
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings(
            booking_id INT AUTO_INCREMENT PRIMARY KEY,
            customer_name VARCHAR(100) NOT NULL,
            contact VARCHAR(15) NOT NULL,
            slot_id INT,
            booking_status VARCHAR(20) NOT NULL,
            booked_at DATETIME NOT NULL,
            FOREIGN KEY(slot_id) REFERENCES slots(slot_id)
        )
        """)

        self.connection.commit()

    # ---------------------------------
    # Slot Operations
    # ---------------------------------

    def insert_slot(self, slot):

        query = """
        INSERT INTO slots
        (service_type, date, start_time, end_time, duration, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        values = (
            slot.service_type,
            slot.date,
            slot.start_time,
            slot.end_time,
            slot.duration,
            slot.status
        )

        self.cursor.execute(query, values)
        self.connection.commit()

    def get_all_slots(self):

        self.cursor.execute("SELECT * FROM slots")
        return self.cursor.fetchall()

    def update_slot_status(self, slot_id, status):

        query = """
        UPDATE slots
        SET status = %s
        WHERE slot_id = %s
        """

        self.cursor.execute(query, (status, slot_id))
        self.connection.commit()

    # ---------------------------------
    # Booking Operations
    # ---------------------------------

    def insert_booking(self, booking):

        query = """
        INSERT INTO bookings
        (customer_name, contact, slot_id, booking_status, booked_at)
        VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            booking.customer_name,
            booking.contact,
            booking.slot_id,
            booking.booking_status,
            booking.booked_at
        )

        self.cursor.execute(query, values)
        self.connection.commit()

    def get_all_bookings(self):

        self.cursor.execute("SELECT * FROM bookings")
        return self.cursor.fetchall()

    def delete_booking(self, booking_id):

        query = """
        DELETE FROM bookings
        WHERE booking_id = %s
        """

        self.cursor.execute(query, (booking_id,))
        self.connection.commit()

    # ---------------------------------
    # Close Connection
    # ---------------------------------

    def close(self):
        self.cursor.close()
        self.connection.close()