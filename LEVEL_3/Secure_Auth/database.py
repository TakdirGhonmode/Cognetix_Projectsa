import mysql.connector
from mysql.connector import Error


class Database:

    def __init__(self):
        self.host = "localhost"
        self.user = "root"
        self.password = "Takdir@1234"
        self.database = "secure_auth_system"

    def get_connection(self):
        try:
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )

            if connection.is_connected():
                return connection

        except Error as e:
            print(f"Database Connection Error: {e}")
            return None