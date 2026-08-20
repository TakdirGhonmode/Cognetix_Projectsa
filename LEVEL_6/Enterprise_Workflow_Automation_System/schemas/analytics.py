from pydantic import BaseModel
from typing import List, Dict, Any

class StageApprovalTime(BaseModel):
    stage_name: str
    avg_hours: float

class TemplateApprovalTime(BaseModel):
    template_id: int
    template_name: str
    avg_hours: float
    stages: List[StageApprovalTime] = []

class ApprovalTimeMetrics(BaseModel):
    overall_avg_hours: float
    templates: List[TemplateApprovalTime] = []

class BottleneckItem(BaseModel):
    stage_name: str
    template_name: str
    pending_tasks_count: int
    overdue_sla_count: int
    avg_wait_hours: float
    status_severity: str # LOW, MEDIUM, HIGH, CRITICAL

class BottleneckMetrics(BaseModel):
    total_bottlenecks: int
    items: List[BottleneckItem] = []

class CompletionRateMetrics(BaseModel):
    total_instances: int
    completed_count: int
    rejected_count: int
    in_progress_count: int
    completion_rate_percent: float
    rejection_rate_percent: float
