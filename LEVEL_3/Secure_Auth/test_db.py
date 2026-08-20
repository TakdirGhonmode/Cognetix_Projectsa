from database import Database

db = Database()
connection = db.get_connection()

if connection:
    print("✅ Connected to MySQL Successfully!")
    connection.close()
else:
    print("❌ Connection Failed!")