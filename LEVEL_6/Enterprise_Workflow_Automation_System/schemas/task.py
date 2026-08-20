from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from schemas.user import UserResponse
from schemas.workflow import WorkflowStageResponse

class TaskActionRequest(BaseModel):
    comments: Optional[str] = None
    reason: Optional[str] = None

class TaskResponse(BaseModel):
    id: int
    instance_id: int
    stage_id: int
    assigned_role: Optional[str] = None
    assigned_department: Optional[str] = None
    assigned_user_id: Optional[int] = None
    status: str
    decision_reason: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    stage: Optional[WorkflowStageResponse] = None
    assigned_user: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)
