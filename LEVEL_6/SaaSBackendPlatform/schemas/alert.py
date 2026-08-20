from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class AlertCreate(BaseModel):
    title: str
    message: str
    severity: Optional[str] = "INFO"  # INFO, WARNING, CRITICAL

class AlertResponse(BaseModel):
    id: int
    organization_id: int
    user_id: int
    title: str
    message: str
    severity: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
