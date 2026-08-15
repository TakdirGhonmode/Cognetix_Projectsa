from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class UsageStatsResponse(BaseModel):
    organization_id: int
    organization_name: str
    current_plan: str
    total_api_calls_today: int
    max_daily_quota: int
    quota_used_percentage: float
    member_count: int
    max_members_allowed: int
    alert: Optional[str] = None

class AnalyticsDashboardResponse(BaseModel):
    organization_id: int
    plan_name: str
    analytics_enabled: bool
    total_requests_30d: int
    active_users_count: int
    metrics: Dict[str, Any]
