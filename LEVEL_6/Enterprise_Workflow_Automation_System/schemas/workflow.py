from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

class WorkflowStageCreate(BaseModel):
    stage_order: int
    name: str
    required_role: Optional[str] = None
    required_department: Optional[str] = None
    assigned_user_id: Optional[int] = None
    approval_required: bool = True
    sla_hours: int = 24

class WorkflowStageResponse(BaseModel):
    id: int
    template_id: int
    stage_order: int
    name: str
    required_role: Optional[str] = None
    required_department: Optional[str] = None
    assigned_user_id: Optional[int] = None
    approval_required: bool
    sla_hours: int

    model_config = ConfigDict(from_attributes=True)

class WorkflowTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    department: str = "General"
    stages: List[WorkflowStageCreate]

class WorkflowTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None
    stages: Optional[List[WorkflowStageCreate]] = None

class WorkflowTemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    department: str
    is_active: bool
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    stages: List[WorkflowStageResponse] = []

    model_config = ConfigDict(from_attributes=True)
