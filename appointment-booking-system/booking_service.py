from models import Booking
from validation import Validation
from database import Database


class BookingService:

    def __init__(self):
        self.db = Database()


    # ---------------------------------
    # Book Appointment
    # ---------------------------------

    def book_slot(self, slots):

        available_slots = [
            slot for slot in slots
            if slot.status == "Available"
        ]

        if len(available_slots) == 0:
            print("\n❌ No Slots Available.")
            return


        print("\n====== Available Slots ======")

        for slot in available_slots:
            slot.display_slot()


        try:
            slot_id = int(input("\nEnter Slot ID : "))

        except ValueError:
            print("❌ Invalid Slot ID.")
            return


        selected_slot = None


        for slot in available_slots:

            if slot.slot_id == slot_id:
                selected_slot = slot
                break


        if selected_slot is None:
            print("❌ Slot Not Found.")
            return



        # Customer Name Validation

        while True:

            customer_name = input("Customer Name : ").strip()

            if Validation.validate_customer_name(customer_name):
                break

            print("❌ Customer name cannot be empty.")



        # Contact Validation

        while True:

            contact = input("Contact Number : ")

            if Validation.validate_contact(contact):
                break

            print("❌ Contact number must contain exactly 10 digits.")



        booking = Booking(
            None,
            customer_name,
            contact,
            selected_slot.slot_id
        )


        self.db.insert_booking(booking)


        self.db.update_slot_status(
            selected_slot.slot_id,
            "Booked"
        )


        selected_slot.status = "Booked"


        print("\n✅ Appointment Booked Successfully!")



    # ---------------------------------
    # View Bookings
    # ---------------------------------

    def view_bookings(self):

        bookings = self.db.get_all_bookings()


        if len(bookings) == 0:

            print("\n❌ No Bookings Found.")
            return



        print("\n========== BOOKINGS ==========")


        for booking in bookings:

            print(f"""
----------------------------------
Booking ID   : {booking[0]}
Customer     : {booking[1]}
Contact      : {booking[2]}
Slot ID      : {booking[3]}
Status       : {booking[4]}
Booked At    : {booking[5]}
----------------------------------
""")



    # ---------------------------------
    # Cancel Booking
    # ---------------------------------

    def cancel_booking(self, slots):

        bookings = self.db.get_all_bookings()


        if len(bookings) == 0:

            print("\n❌ No Bookings Found.")
            return



        self.view_bookings()



        try:

            booking_id = int(
                input("\nEnter Booking ID to Cancel : ")
            )


        except ValueError:

            print("❌ Invalid Booking ID.")
            return



        booking_found = None



        for booking in bookings:

            if booking[0] == booking_id:

                booking_found = booking
                break



        if booking_found is None:

            print("❌ Booking Not Found.")
            return



        # Make Slot Available Again

        self.db.update_slot_status(
            booking_found[3],
            "Available"
        )



        for slot in slots:

            if slot.slot_id == booking_found[3]:

                slot.status = "Available"
                slot.customer_name = None
                slot.contact = None

                break



        # Delete Booking Record

        self.db.delete_booking(booking_id)



        print("\n✅ Booking Cancelled Successfully!")