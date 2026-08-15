from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class SubscriptionPlanResponse(BaseModel):
    id: int
    name: str
    price_monthly: float
    max_users: int
    max_alerts: int
    max_projects: int
    max_api_calls_per_day: int
    has_analytics: bool
    has_export: bool
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class TenantSubscriptionResponse(BaseModel):
    id: int
    organization_id: int
    plan_id: int
    plan: SubscriptionPlanResponse
    status: str
    start_date: datetime
    end_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ChangePlanRequest(BaseModel):
    plan_name: str  # free, basic, premium
