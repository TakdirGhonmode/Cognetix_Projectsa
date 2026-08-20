# import bcrypt

# from database import Database
# from models import User


# class AuthService:

#     def __init__(self):
#       self.db = Database()
#       self.current_user = None   

#     def username_exists(self, username):
#         connection = self.db.get_connection()

#         cursor = connection.cursor()

#         query = "SELECT * FROM users WHERE username = %s"

#         cursor.execute(query, (username,))

#         user = cursor.fetchone()

#         cursor.close()
#         connection.close()

#         return user is not None

#     def validate_password(self, password):

#         if len(password) < 8:
#             return False

#         return True

#     def hash_password(self, password):

#         salt = bcrypt.gensalt()

#         hashed = bcrypt.hashpw(password.encode(), salt)

#         return hashed.decode()

#     def save_user(self, user):

#         connection = self.db.get_connection()

#         cursor = connection.cursor()

#         query = """
#             INSERT INTO users(username, password, role)
#             VALUES(%s, %s, %s)
#         """

#         cursor.execute(
#             query,
#             (
#                 user.username,
#                 user.password,
#                 user.role
#             )
#         )

#         connection.commit()

#         cursor.close()
#         connection.close()

#     def register_user(self, username, password, role):

#         if self.username_exists(username):
#             print("Username already exists.")
#             return

#         if not self.validate_password(password):
#             print("Password must be at least 8 characters.")
#             return

#         hashed_password = self.hash_password(password)

#         user = User(
#             username=username,
#             password=hashed_password,
#             role=role
#         )

#         self.save_user(user)

#         print("User Registered Successfully!")
#     def get_user_by_username(self, username):

#         connection = self.db.get_connection()

#         cursor = connection.cursor(dictionary=True)

#         query = "SELECT * FROM users WHERE username = %s"

#         cursor.execute(query, (username,))

#         user = cursor.fetchone()

#         cursor.close()
#         connection.close()

#         return user

#     def verify_password(self, entered_password, stored_password):

#         return bcrypt.checkpw(
#             entered_password.encode(),
#             stored_password.encode()
#         )

#     def login_user(self, username, password):

#         user = self.get_user_by_username(username)

#         if user is None:
#             print("User not found.")
#             return None

#         if self.verify_password(password, user["password"]):

#             print("Login Successful!")

#             return user

#         else:

#             print("Invalid Password!")

#             return None

#         if self.verify_password(password, user["password"]):
#                self.current_user = user
#                print("Login Successful!")
#                return user
#     def logout_user(self):

#       if self.current_user is None:
#          print("No user is currently logged in.")
#          return 
#       print(f"{self.current_user['username']} logged out successfully.")
#       self.current_user = None
import bcrypt

from database import Database
from models import User
from logger import Logger


class AuthService:

    def __init__(self):
        self.db = Database()
        self.logger = Logger()
        self.current_user = None

    # ------------------------------
    # Registration Methods
    # ------------------------------

    def username_exists(self, username):

        connection = self.db.get_connection()

        cursor = connection.cursor()

        query = "SELECT * FROM users WHERE username = %s"

        cursor.execute(query, (username,))

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        return user is not None

    def validate_password(self, password):

        return len(password) >= 8

    def hash_password(self, password):

        salt = bcrypt.gensalt()

        hashed = bcrypt.hashpw(password.encode(), salt)

        return hashed.decode()

    def save_user(self, user):

        connection = self.db.get_connection()

        cursor = connection.cursor()

        query = """
        INSERT INTO users(username, password, role)
        VALUES(%s, %s, %s)
        """

        cursor.execute(
            query,
            (
                user.username,
                user.password,
                user.role
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

    def register_user(self, username, password, role):

        if self.username_exists(username):
            print("Username already exists.")
            return

        if not self.validate_password(password):
            print("Password must be at least 8 characters.")
            return

        if role not in ["Admin", "User"]:
            print("Role must be Admin or User.")
            return

        hashed_password = self.hash_password(password)

        user = User(
            username=username,
            password=hashed_password,
            role=role
        )

        self.save_user(user)

        self.logger.registration_success(username)

        print("User Registered Successfully!")

    # ------------------------------
    # Login Methods
    # ------------------------------

    def get_user_by_username(self, username):

        connection = self.db.get_connection()

        cursor = connection.cursor(dictionary=True)

        query = "SELECT * FROM users WHERE username = %s"

        cursor.execute(query, (username,))

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        return user

    def verify_password(self, entered_password, stored_password):

        return bcrypt.checkpw(
            entered_password.encode(),
            stored_password.encode()
        )

    def login_user(self, username, password):

        user = self.get_user_by_username(username)

        if user is None:
            print("User not found.")
            self.logger.login_failed(username)
            return None

        if self.verify_password(password, user["password"]):

            self.current_user = user

            self.logger.login_success(username)

            print("Login Successful!")

            return user

        else:

            self.logger.login_failed(username)

            print("Invalid Password!")

            return None

    # ------------------------------
    # Logout
    # ------------------------------

    def logout_user(self):

        if self.current_user is None:
            print("No user is currently logged in.")
            return

        username = self.current_user["username"]

        self.logger.logout_success(username)

        print(f"{username} logged out successfully.")

        self.current_user = None