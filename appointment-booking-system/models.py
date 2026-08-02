from datetime import datetime


class Slot:

    def __init__(self, slot_id, service_type, date, start_time, end_time, duration):
        self.slot_id = slot_id
        self.service_type = service_type
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration
        self.status = "Available"
        self.customer_name = None
        self.contact = None

    def display_slot(self):
        print("\n---------- SLOT DETAILS ----------")
        print(f"Slot ID      : {self.slot_id}")
        print(f"Service Type : {self.service_type}")
        print(f"Date         : {self.date}")
        print(f"Start Time   : {self.start_time}")
        print(f"End Time     : {self.end_time}")
        print(f"Duration     : {self.duration} Minutes")
        print(f"Status       : {self.status}")
        print("----------------------------------")


class Booking:

    def __init__(self, booking_id, customer_name, contact, slot_id):
        self.booking_id = booking_id
        self.customer_name = customer_name
        self.contact = contact
        self.slot_id = slot_id
        self.booking_status = "Booked"

        # MySQL DATETIME format
        self.booked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def display_booking(self):
        print("\n-------- BOOKING DETAILS --------")
        print(f"Booking ID   : {self.booking_id}")
        print(f"Customer     : {self.customer_name}")
        print(f"Contact      : {self.contact}")
        print(f"Slot ID      : {self.slot_id}")
        print(f"Status       : {self.booking_status}")
        print(f"Booked At    : {self.booked_at}")
        print("---------------------------------")