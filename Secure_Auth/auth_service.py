import bcrypt

from database import Database
from models import User


class AuthService:

    def __init__(self):
        self.db = Database()

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

        if len(password) < 8:
            return False

        return True

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

        hashed_password = self.hash_password(password)

        user = User(
            username=username,
            password=hashed_password,
            role=role
        )

        self.save_user(user)

        print("User Registered Successfully!")