from auth_service import AuthService
from role_manager import RoleManager

auth = AuthService()

while True:

    print("\n========== SECURE AUTH SYSTEM ==========")
    print("1. Register")
    print("2. Login")
    print("3. Admin Dashboard")
    print("4. User Dashboard")
    print("5. Logout")
    print("6. Exit")

    choice = input("Enter your choice: ")

    # ---------------- Register ----------------
    if choice == "1":

        username = input("Enter Username: ")
        password = input("Enter Password: ")
        role = input("Enter Role (Admin/User): ")

        auth.register_user(username, password, role)

    # ---------------- Login ----------------
    elif choice == "2":

        username = input("Enter Username: ")
        password = input("Enter Password: ")

        auth.login_user(username, password)

    # ---------------- Admin Dashboard ----------------
    elif choice == "3":

        if auth.current_user is None:
            print("Please login first.")

        elif RoleManager.is_admin(auth.current_user):

            print("\n========== ADMIN DASHBOARD ==========")
            print(f"Welcome Admin : {auth.current_user['username']}")
            print("-------------------------------------")
            print("1. Manage Users")
            print("2. View Authentication Logs")
            print("3. System Settings")

        else:
            print("Access Denied! Only Admin can access this dashboard.")

    # ---------------- User Dashboard ----------------
    elif choice == "4":

        if auth.current_user is None:
            print("Please login first.")

        elif RoleManager.is_user(auth.current_user):

            print("\n========== USER DASHBOARD ==========")
            print(f"Welcome {auth.current_user['username']}")
            print("-------------------------------------")
            print("1. View Profile")
            print("2. Change Password")
            print("3. Logout")

        else:
            print("Access Denied! Only User can access this dashboard.")

    # ---------------- Logout ----------------
    elif choice == "5":

        auth.logout_user()

    # ---------------- Exit ----------------
    elif choice == "6":

        print("Thank You for using Secure Auth System.")
        break

    else:
        print("Invalid Choice!")