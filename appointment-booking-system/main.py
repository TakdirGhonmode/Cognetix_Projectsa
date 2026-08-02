from slot_manager import SlotManager
from booking_service import BookingService
from reports import Reports


slot_manager = SlotManager()
booking_service = BookingService()
report = Reports()


while True:

    print("\n===== Appointment Booking System =====")
    print("1. Create Slot")
    print("2. View Slots")
    print("3. Book Appointment")
    print("4. View Bookings")
    print("5. Cancel Booking")
    print("6. Generate Summary Report")
    print("7. Generate Booking Details")
    print("8. Exit")


    choice = input("Enter Choice : ")



    if choice == "1":

        slot_manager.create_slot()



    elif choice == "2":

        slot_manager.view_slots()



    elif choice == "3":

        # Load latest slots from database

        slot_manager.load_slots()

        booking_service.book_slot(
            slot_manager.slots
        )



    elif choice == "4":

        booking_service.view_bookings()



    elif choice == "5":

        # Load latest slots before cancellation

        slot_manager.load_slots()

        booking_service.cancel_booking(
            slot_manager.slots
        )



    elif choice == "6":

        report.booking_summary()



    elif choice == "7":

        report.booking_details()



    elif choice == "8":

        print("\nThank You!")
        break



    else:

        print("❌ Invalid Choice.")