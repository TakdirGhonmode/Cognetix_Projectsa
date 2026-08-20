from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


# User Schemas
class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "User"


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Ticket Schemas
class TicketCreate(BaseModel):
    customer_name: str
    issue_description: str
    category: str
    priority: Optional[str] = "Low"


class TicketUpdate(BaseModel):
    issue_description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[int] = None


class TicketResponse(BaseModel):
    id: int
    customer_name: str
    issue_description: str
    category: str
    priority: str
    status: str
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    created_by: Optional[int] = None
    assigned_to: Optional[int] = None

    class Config:
        from_attributes = True


class TicketHistoryResponse(BaseModel):
    id: int
    ticket_id: int
    action: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    performed_by: Optional[int] = None
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


# API Response Wrapper Schema
class APIResponse(BaseModel):
    status: str = "success"
    message: str
    data: Optional[Any] = None