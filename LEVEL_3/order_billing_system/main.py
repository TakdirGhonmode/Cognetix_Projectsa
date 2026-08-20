from order_manager import OrderManager
from billing import Billing
from payment import Payment
from reports import Reports

order = OrderManager()
bill = Billing()
payment = Payment()
report = Reports()

while True:

    print("""
========== ORDER BILLING SYSTEM ==========

1.Create Order
2.View Orders
3.Search Order
4.Update Order Status
5.Delete Order
6.Generate Invoice
7.Record Payment
8.Transaction History
9.Exit
""")

    choice = int(input("Enter Choice : "))

    if choice == 1:
        order.create_order()

    elif choice == 2:
        order.view_orders()

    elif choice == 3:
        order.search_order()

    elif choice == 4:
        order.update_order_status()

    elif choice == 5:
        order.delete_order()

    elif choice == 6:
        bill.generate_invoice()

    elif choice == 7:
        payment.record_payment()

    elif choice == 8:
        report.transaction_history()

    elif choice == 9:
        print("Thank You!")
        break

    else:
        print("Invalid Choice.")