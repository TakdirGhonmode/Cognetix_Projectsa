from database import Database

db = Database()

db.create_tables()

print("✅ MySQL Connected Successfully!")

db.close()