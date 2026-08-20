from customer import CustomerManager
from billing import Billing
from invoice_generator import InvoiceGenerator


customer_manager = CustomerManager()
billing = Billing()
invoice_generator = InvoiceGenerator()


while True:

    print("\n" + "=" * 45)
    print(" Professional Invoice & Billing Generator")
    print("=" * 45)
    print("1. Add Customer")
    print("2. View Customers")
    print("3. Create Invoice")
    print("4. View Invoice History")
    print("5. Search Invoice")
    print("6. Exit")

    choice = input("\nEnter Your Choice : ")

    if choice == "1":

        customer_manager.add_customer()

    elif choice == "2":

        customer_manager.view_customers()

    elif choice == "3":

        customer_id = input("\nEnter Customer ID : ")

        customer = customer_manager.search_customer(customer_id)

        if customer is None:
            print("Customer Not Found.")
            continue

        billing.clear_items()

        billing.add_item()

        billing.display_items()

        bill = billing.bill_summary()

        if bill is not None:
            invoice_generator.create_invoice(customer_id, bill)

    elif choice == "4":

        invoice_generator.view_invoices()

    elif choice == "5":

        invoice_number = input("Enter Invoice Number : ")

        invoice_generator.search_invoice(invoice_number)

    elif choice == "6":

        print("\nThank You!")
        break

    else:

        print("Invalid Choice.")