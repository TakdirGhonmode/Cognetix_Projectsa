from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, declarative_base

# -----------------------------
# MySQL Database Configuration
# -----------------------------
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username="root",
    password="Takdir@1234",
    host="localhost",
    port=3306,
    database="product_management_api"
)

# Create Engine
engine = create_engine(
    DATABASE_URL,
    echo=True
)

# Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base Class
Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()