import json
import os


class Customer:
    def __init__(self, customer_id, name, email, phone, address):
        self.customer_id = customer_id
        self.name = name
        self.email = email
        self.phone = phone
        self.address = address

    def to_dict(self):
        return {
            "customer_id": self.customer_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address
        }

class CustomerManager:

    FILE_NAME = "invoices.json"

    def load_data(self):

        if not os.path.exists(self.FILE_NAME):

            data = {
                "customers": [],
                "invoices": []
            }

            with open(self.FILE_NAME, "w") as file:
                json.dump(data, file, indent=4)

            return data

        with open(self.FILE_NAME, "r") as file:

            try:
                return json.load(file)

            except json.JSONDecodeError:
                return {
                    "customers": [],
                    "invoices": []
                }

    def save_data(self, data):

        with open(self.FILE_NAME, "w") as file:
            json.dump(data, file, indent=4)

    def add_customer(self):

        data = self.load_data()

        while True:

            customer_id = input("Enter Customer ID : ").strip()

            if customer_id == "":
                print("Customer ID cannot be empty.")
                continue

            duplicate = False

            for customer in data["customers"]:
                if customer["customer_id"] == customer_id:
                    duplicate = True
                    break

            if duplicate:
                print("Customer ID already exists. Enter another ID.")
            else:
                break

        while True:

            name = input("Enter Name : ").strip()

            if name == "":
                print("Name cannot be empty.")

            elif not any(ch.isalpha() for ch in name):
                print("Name must contain at least one alphabet.")

            else:
                break

        while True:

            email = input("Enter Email : ").strip()

            if "@" not in email or "." not in email:
                print("Invalid Email.")

            else:
                break

        while True:

            phone = input("Enter Phone : ").strip()

            if not phone.isdigit():
                print("Phone number must contain only digits.")

            elif len(phone) != 10:
                print("Phone number must contain exactly 10 digits.")

            else:
                break

        while True:

            address = input("Enter Address : ").strip()

            if address == "":
                print("Address cannot be empty.")
            else:
                break

        customer = Customer(
            customer_id,
            name,
            email,
            phone,
            address
        )

        data["customers"].append(customer.to_dict())

        self.save_data(data)

        print("\nCustomer Added Successfully.")

    def view_customers(self):

        data = self.load_data()

        if not data["customers"]:
            print("\nNo Customers Found.")
            return

        print("\n========== CUSTOMER LIST ==========")

        for customer in data["customers"]:

            print("-" * 40)
            print("Customer ID :", customer["customer_id"])
            print("Name        :", customer["name"])
            print("Email       :", customer["email"])
            print("Phone       :", customer["phone"])
            print("Address     :", customer["address"])

    def search_customer(self, customer_id):

        data = self.load_data()

        for customer in data["customers"]:

            if customer["customer_id"] == customer_id:
                return customer

        return None