from database import Database


class Reports:

    def __init__(self, db):
        self.db = db

   

    # ---------------------------------
    # Booking Summary Report
    # ---------------------------------

    def booking_summary(self):

        slots = self.db.get_all_slots()
        bookings = self.db.get_all_bookings()


        total_slots = len(slots)
        total_bookings = len(bookings)


        available_slots = 0
        booked_slots = 0


        for slot in slots:

            if slot[6] == "Available":
                available_slots += 1

            elif slot[6] == "Booked":
                booked_slots += 1



        print("\n========== BOOKING REPORT ==========")

        print(f"Total Slots      : {total_slots}")
        print(f"Available Slots  : {available_slots}")
        print(f"Booked Slots     : {booked_slots}")
        print(f"Total Bookings   : {total_bookings}")

        print("------------------------------------")



    # ---------------------------------
    # Booking Details Report
    # ---------------------------------

    def booking_details(self):

        bookings = self.db.get_all_bookings()


        if len(bookings) == 0:

            print("\n❌ No Booking Records Found.")
            return



        print("\n========== BOOKING DETAILS ==========")


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