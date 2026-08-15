from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional, Dict, Any
from schemas.user import UserResponse
from schemas.workflow import WorkflowStageResponse
from schemas.task import TaskResponse

class WorkflowInstanceCreate(BaseModel):
    template_id: int
    title: str
    payload: Optional[Dict[str, Any]] = None

class WorkflowInstanceResponse(BaseModel):
    id: int
    template_id: int
    title: str
    initiator_id: int
    current_stage_id: Optional[int] = None
    status: str
    payload: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    initiator: Optional[UserResponse] = None
    current_stage: Optional[WorkflowStageResponse] = None
    tasks: List[TaskResponse] = []

    model_config = ConfigDict(from_attributes=True)
