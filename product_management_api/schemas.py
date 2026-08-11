from pydantic import BaseModel, Field
from typing import Optional


# -----------------------------
# Product Create Schema
# -----------------------------
class ProductCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    product_name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    quantity: int = Field(..., ge=0)
    category: str = Field(..., min_length=2, max_length=100)


# -----------------------------
# Product Update Schema
# -----------------------------
class ProductUpdate(BaseModel):
    product_name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, min_length=2, max_length=100)


# -----------------------------
# Product Response Schema
# -----------------------------
class ProductResponse(BaseModel):
    product_id: int
    product_name: str
    description: Optional[str]
    price: float
    quantity: int
    category: str

    class Config:
        from_attributes = True


# -----------------------------
# Login Schema
# -----------------------------
class Login(BaseModel):
    username: str
    password: str


# -----------------------------
# User Create Schema
# -----------------------------
class UserCreate(BaseModel):
    username: str
    password: str
    role: str