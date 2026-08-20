from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Generic, TypeVar, Any, List
from datetime import datetime

T = TypeVar("T")


# -----------------------------
# Product Schemas
# -----------------------------
class ProductCreate(BaseModel):
    product_id: int = Field(..., gt=0, description="Unique product ID (> 0)")
    product_name: str = Field(..., min_length=1, max_length=100, description="Name of product")
    description: Optional[str] = Field(None, description="Detailed product description")
    price: float = Field(..., gt=0, description="Product price must be greater than zero (> 0)")
    quantity: int = Field(..., ge=0, description="Product quantity must be non-negative (>= 0)")
    category: str = Field(..., min_length=1, max_length=100, description="Category name")

    @field_validator("product_name", "category")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty or blank")
        return cleaned


class ProductUpdate(BaseModel):
    product_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, min_length=1, max_length=100)

    @field_validator("product_name", "category")
    @classmethod
    def validate_non_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            cleaned = value.strip()
            if not cleaned:
                raise ValueError("Field cannot be empty or blank")
            return cleaned
        return value


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    product_name: str
    description: Optional[str] = None
    price: float
    quantity: int
    category: str


# -----------------------------
# User & Auth Schemas
# -----------------------------
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4, max_length=100)
    role: str = Field("user", description="Role: 'user' or 'admin'")

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        role = value.lower().strip()
        if role not in ["user", "admin"]:
            raise ValueError("Role must be either 'user' or 'admin'")
        return role


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


# -----------------------------
# Transaction History Schema
# -----------------------------
class TransactionHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    product_id: int
    user_id: Optional[int] = None
    timestamp: Optional[datetime] = None


# -----------------------------
# API Standard Envelope Response
# -----------------------------
class APIResponse(BaseModel, Generic[T]):
    status: str = "success"
    message: str
    data: Optional[T] = None


class APIErrorResponse(BaseModel):
    status: str = "error"
    message: str
    details: Optional[Any] = None