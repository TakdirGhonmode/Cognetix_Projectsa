from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional, List

class OrganizationCreate(BaseModel):
    name: str
    slug: str

class OrganizationResponse(BaseModel):
    id: int
    name: str
    slug: str
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MemberAdd(BaseModel):
    email: EmailStr
    role: str = "USER"  # ADMIN, ORG_OWNER, MANAGER, USER

class MemberResponse(BaseModel):
    id: int
    user_id: int
    email: str
    full_name: Optional[str] = None
    role: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)
