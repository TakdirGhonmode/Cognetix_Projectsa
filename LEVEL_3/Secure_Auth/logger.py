from database import Database


class Logger:

    def __init__(self):
        self.db = Database()

    def log(self, username, action, status):

        connection = self.db.get_connection()

        if connection is None:
            print("Database connection failed.")
            return

        cursor = connection.cursor()

        query = """
        INSERT INTO auth_logs (username, action, status)
        VALUES (%s, %s, %s)
        """

        try:
            cursor.execute(query, (username, action, status))
            connection.commit()

        except Exception as e:
            print("Logging Error:", e)

        finally:
            cursor.close()
            connection.close()

    def registration_success(self, username):
        self.log(username, "REGISTER", "SUCCESS")

    def login_success(self, username):
        self.log(username, "LOGIN", "SUCCESS")

    def login_failed(self, username):
        self.log(username, "LOGIN", "FAILED")

    def logout_success(self, username):
        self.log(username, "LOGOUT", "SUCCESS")

    def access_denied(self, username):
        self.log(username, "ACCESS", "DENIED")