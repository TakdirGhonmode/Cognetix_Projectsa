from datetime import datetime
from models import Slot
from validation import Validation
from database import Database


class SlotManager:

    def __init__(self, db):
        self.db = db
        self.slots = []

    # ---------------------------------
    # Load Slots From Database
    # ---------------------------------

    def load_slots(self):

      slots_data = self.db.get_all_slots()

      self.slots = []

      for slot in slots_data:

          obj = Slot(
              slot[0],
              slot[1],
              slot[2],
              slot[3],
              slot[4],
              slot[5]
            )

          obj.status = slot[6]

          self.slots.append(obj)

    # ---------------------------------
    # Create Slot
    # ---------------------------------

    def create_slot(self):

        print("\n===== Create New Slot =====")

        while True:
            service_type = input("Enter Service Type : ")

            if Validation.validate_service(service_type):
                break

            print("❌ Service name cannot be empty.")

        while True:
            date = input("Enter Date (DD-MM-YYYY): ")

            if Validation.validate_date(date):
                break

            print("❌ Invalid date or past date.")

        while True:
            start_time = input("Enter Start Time (HH:MM): ")

            if Validation.validate_time(start_time):
                break

            print("❌ Invalid Start Time.")

        while True:
            end_time = input("Enter End Time (HH:MM): ")

            if Validation.validate_time(end_time):
                break

            print("❌ Invalid End Time.")

        if not Validation.validate_working_hours(start_time, end_time):
            print("❌ Time must be between 09:00 and 18:00.")
            return

        while True:
            duration = input("Enter Duration (Minutes): ")

            if Validation.validate_duration(duration):
                duration = int(duration)
                break

            print("❌ Invalid Duration.")

        # Convert DD-MM-YYYY to YYYY-MM-DD for MySQL
        mysql_date = datetime.strptime(
            date,
            "%d-%m-%Y"
        ).strftime("%Y-%m-%d")


        slot = Slot(
            None,
            service_type,
            mysql_date,
            start_time,
            end_time,
            duration
        )


        self.db.insert_slot(slot)

        print("\n✅ Slot Created Successfully!")


    # ---------------------------------
    # View Slots
    # ---------------------------------

    def view_slots(self):

     slots = self.db.get_all_slots()

     print("\nDEBUG DATA:")
     print(slots)   # <-- Add these two lines

     if len(slots) == 0:
         print("\n❌ No Slots Available.")
         return

     print("\n========== AVAILABLE SLOTS ==========")

     for slot in slots:

         print(f"""
----------------------------------
Slot ID      : {slot[0]}
Service Type : {slot[1]}
Date         : {slot[2]}
Start Time   : {slot[3]}
End Time     : {slot[4]}
Duration     : {slot[5]} Minutes
Status       : {slot[6]}
----------------------------------
""")