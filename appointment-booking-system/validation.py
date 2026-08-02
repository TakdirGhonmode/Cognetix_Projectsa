from datetime import datetime


class Validation:

    @staticmethod
    def validate_service(service):
        return len(service.strip()) > 0

    @staticmethod
    def validate_customer_name(name):
        return len(name.strip()) > 0

    @staticmethod
    def validate_date(date):
        try:
            booking_date = datetime.strptime(date, "%d-%m-%Y").date()

            if booking_date < datetime.today().date():
                return False

            return True

        except ValueError:
            return False

    @staticmethod
    def validate_time(time):
        try:
            datetime.strptime(time, "%H:%M")
            return True

        except ValueError:
            return False

    @staticmethod
    def validate_working_hours(start_time, end_time):
        try:
            start = datetime.strptime(start_time, "%H:%M")
            end = datetime.strptime(end_time, "%H:%M")

            office_start = datetime.strptime("09:00", "%H:%M")
            office_end = datetime.strptime("18:00", "%H:%M")

            if start < office_start:
                return False

            if end > office_end:
                return False

            if end <= start:
                return False

            return True

        except ValueError:
            return False

    @staticmethod
    def validate_duration(duration):
        try:
            duration = int(duration)

            if duration <= 0:
                return False

            return True

        except ValueError:
            return False

    @staticmethod
    def validate_contact(contact):
        if len(contact) != 10:
            return False

        return contact.isdigit()