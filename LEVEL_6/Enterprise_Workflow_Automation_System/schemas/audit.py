from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from schemas.user import UserResponse

class AuditLogResponse(BaseModel):
    id: int
    instance_id: int
    stage_id: Optional[int] = None
    actor_id: int
    action: str
    details: Optional[str] = None
    previous_hash: str
    current_hash: str
    timestamp: datetime

    actor: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)

class AuditVerifyResponse(BaseModel):
    is_valid: bool
    total_records: int
    corrupted_records: List[int] = []
    message: str
