from sqlalchemy import Column, Integer, String, Text, DECIMAL, DateTime
from sqlalchemy.sql import func
from database import Base


# -----------------------------
# Product Table
# -----------------------------
class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(DECIMAL(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    category = Column(String(100), nullable=False)


# -----------------------------
# User Table
# -----------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)


# -----------------------------
# Transaction History Table
# -----------------------------
class TransactionHistory(Base):
    __tablename__ = "transaction_history"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(50), nullable=False)
    product_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())