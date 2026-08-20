class Billing:

    def __init__(self):
        self.items = []

    def add_item(self):

        while True:

            item_name = input("Enter Item Name : ").strip()

            try:
                quantity = int(input("Enter Quantity : "))

                if quantity <= 0:
                    print("Quantity must be greater than 0.")
                    continue

            except ValueError:
                print("Invalid Quantity.")
                continue

            try:
                unit_price = float(input("Enter Unit Price : "))

                if unit_price < 0:
                    print("Unit Price cannot be negative.")
                    continue

            except ValueError:
                print("Invalid Unit Price.")
                continue

            total = quantity * unit_price

            item = {
                "item_name": item_name,
                "quantity": quantity,
                "unit_price": unit_price,
                "total": total
            }

            self.items.append(item)

            choice = input("Add Another Item (y/n) : ").lower()

            if choice != "y":
                break

    def display_items(self):

        if not self.items:
            print("\nNo Items Added.")
            return

        print("\n" + "=" * 65)
        print(f"{'Item Name':20}{'Qty':>10}{'Price':>15}{'Total':>15}")
        print("=" * 65)

        for item in self.items:

            print(
                f"{item['item_name']:20}"
                f"{item['quantity']:>10}"
                f"{item['unit_price']:>15.2f}"
                f"{item['total']:>15.2f}"
            )

        print("=" * 65)

    def calculate_subtotal(self):

        subtotal = 0

        for item in self.items:
            subtotal += item["total"]

        return subtotal

    def calculate_tax(self, tax_percentage):

        subtotal = self.calculate_subtotal()

        return subtotal * tax_percentage / 100

    def calculate_discount(self, discount_percentage):

        subtotal = self.calculate_subtotal()

        return subtotal * discount_percentage / 100

    def calculate_final_amount(self, tax_percentage, discount_percentage):

        subtotal = self.calculate_subtotal()

        tax = self.calculate_tax(tax_percentage)

        discount = self.calculate_discount(discount_percentage)

        return subtotal + tax - discount

    def bill_summary(self):

        if not self.items:
            print("No Items Available.")
            return None

        tax_percentage = float(input("Enter Tax Percentage : "))
        discount_percentage = float(input("Enter Discount Percentage : "))

        subtotal = self.calculate_subtotal()
        tax = self.calculate_tax(tax_percentage)
        discount = self.calculate_discount(discount_percentage)
        final_amount = self.calculate_final_amount(
            tax_percentage,
            discount_percentage
        )

        print("\n========== BILL SUMMARY ==========")
        print(f"Subtotal          : {subtotal:.2f}")
        print(f"Tax Amount        : {tax:.2f}")
        print(f"Discount Amount   : {discount:.2f}")
        print("----------------------------------")
        print(f"Final Amount      : {final_amount:.2f}")

        return {
            "items": self.items,
            "subtotal": subtotal,
            "tax_percentage": tax_percentage,
            "tax_amount": tax,
            "discount_percentage": discount_percentage,
            "discount_amount": discount,
            "final_amount": final_amount
        }

    def clear_items(self):
        self.items.clear()