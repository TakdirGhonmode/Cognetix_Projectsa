class RoleManager:

    @staticmethod
    def is_admin(user):
        """
        Check if the logged-in user is an Admin.
        """
        if user is None:
            return False

        return user["role"] == "Admin"

    @staticmethod
    def is_user(user):
        """
        Check if the logged-in user is a User.
        """
        if user is None:
            return False

        return user["role"] == "User"

    @staticmethod
    def has_permission(user, required_role):
        """
        Generic role checker.
        Example:
            has_permission(user, "Admin")
            has_permission(user, "User")
        """
        if user is None:
            return False

        return user["role"] == required_role

    @staticmethod
    def display_dashboard(user):
        """
        Display dashboard based on role.
        """
        if user is None:
            print("Please login first.")
            return

        if user["role"] == "Admin":
            print("\n========== ADMIN DASHBOARD ==========")
            print(f"Welcome Admin, {user['username']}")
            print("-------------------------------------")
            print("1. View All Users")
            print("2. View Authentication Logs")
            print("3. Logout")

        elif user["role"] == "User":
            print("\n========== USER DASHBOARD ==========")
            print(f"Welcome, {user['username']}")
            print("-------------------------------------")
            print("1. View Profile")
            print("2. Logout")

        else:
            print("Invalid Role!")