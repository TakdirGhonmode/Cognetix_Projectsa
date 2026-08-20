import json
import os
from datetime import datetime


class InvoiceGenerator:

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

    def generate_invoice_number(self):

        data = self.load_data()

        invoice_count = len(data["invoices"]) + 1

        year = datetime.now().year

        return f"INV-{year}-{invoice_count:03d}"

    def get_customer(self, customer_id):

        data = self.load_data()

        for customer in data["customers"]:

            if customer["customer_id"] == customer_id:
                return customer

        return None

    def create_invoice(self, customer_id, bill):

        customer = self.get_customer(customer_id)

        if customer is None:
            print("Customer Not Found.")
            return

        data = self.load_data()

        invoice = {
            "invoice_number": self.generate_invoice_number(),
            "date": datetime.now().strftime("%d-%m-%Y"),
            "customer": customer,
            "items": bill["items"],
            "subtotal": bill["subtotal"],
            "tax_percentage": bill["tax_percentage"],
            "tax_amount": bill["tax_amount"],
            "discount_percentage": bill["discount_percentage"],
            "discount_amount": bill["discount_amount"],
            "final_amount": bill["final_amount"]
        }

        data["invoices"].append(invoice)

        self.save_data(data)

        self.generate_text_invoice(invoice)

        print("\nInvoice Generated Successfully.")
        print("Invoice Number :", invoice["invoice_number"])

    def generate_text_invoice(self, invoice):

        file_name = invoice["invoice_number"] + ".txt"

        with open(file_name, "w") as file:

            file.write("=========================================\n")
            file.write("        PROFESSIONAL INVOICE\n")
            file.write("=========================================\n\n")

            file.write(f"Invoice Number : {invoice['invoice_number']}\n")
            file.write(f"Date           : {invoice['date']}\n\n")

            customer = invoice["customer"]

            file.write("Customer Details\n")
            file.write("-----------------------------------------\n")
            file.write(f"Customer ID : {customer['customer_id']}\n")
            file.write(f"Name        : {customer['name']}\n")
            file.write(f"Email       : {customer['email']}\n")
            file.write(f"Phone       : {customer['phone']}\n")
            file.write(f"Address     : {customer['address']}\n\n")

            file.write("Items\n")
            file.write("-----------------------------------------\n")

            for item in invoice["items"]:

                file.write(
                    f"{item['item_name']} | "
                    f"Qty : {item['quantity']} | "
                    f"Price : {item['unit_price']} | "
                    f"Total : {item['total']}\n"
                )

            file.write("\n-----------------------------------------\n")
            file.write(f"Subtotal          : {invoice['subtotal']:.2f}\n")
            file.write(f"Tax Amount        : {invoice['tax_amount']:.2f}\n")
            file.write(f"Discount Amount   : {invoice['discount_amount']:.2f}\n")
            file.write(f"Final Amount      : {invoice['final_amount']:.2f}\n")
            file.write("=========================================\n")

    def view_invoices(self):

        data = self.load_data()

        if not data["invoices"]:
            print("\nNo Invoice Found.")
            return

        for invoice in data["invoices"]:

            print("\n=========================================")
            print("Invoice Number :", invoice["invoice_number"])
            print("Date           :", invoice["date"])
            print("Customer       :", invoice["customer"]["name"])
            print("Final Amount   :", invoice["final_amount"])
            print("=========================================")

    def search_invoice(self, invoice_number):

        data = self.load_data()

        for invoice in data["invoices"]:

            if invoice["invoice_number"] == invoice_number:

                print("\n========== Invoice Found ==========")
                print("Invoice Number :", invoice["invoice_number"])
                print("Date           :", invoice["date"])
                print("Customer       :", invoice["customer"]["name"])
                print("Final Amount   :", invoice["final_amount"])
                return

        print("Invoice Not Found.")