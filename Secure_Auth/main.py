from auth_service import AuthService

auth = AuthService()

while True:

    print("\n===== Secure Auth System =====")
    print("1. Register")
    print("2. Exit")

    choice = input("Enter your choice: ")

    if choice == "1":

        username = input("Enter Username: ")
        password = input("Enter Password: ")
        role = input("Enter Role (Admin/User): ")

        auth.register_user(username, password, role)

    elif choice == "2":
        print("Thank You!")
        break

    else:
        print("Invalid Choice!")