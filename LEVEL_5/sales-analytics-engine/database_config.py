import os
from urllib.parse import quote_plus

# MySQL Database Configuration
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "Takdir@1234")
DB_NAME = os.environ.get("DB_NAME", "sales_analytics_db")

def get_connection_string(include_db: bool = True) -> str:
    """
    Constructs MySQL SQLAlchemy connection URI string using PyMySQL driver.
    URL encodes password to handle special characters (e.g. '@', '#', '$').
    """
    encoded_password = quote_plus(DB_PASSWORD)
    if include_db:
        return f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}"
