from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from schemas.analytics import ApprovalTimeMetrics, BottleneckMetrics, CompletionRateMetrics
from auth.rbac import get_current_active_user
from services.analytics_service import calculate_approval_times, calculate_bottlenecks, calculate_completion_rates

router = APIRouter(prefix="/analytics", tags=["Monitoring & Analytics"])

@router.get("/approval-time", response_model=ApprovalTimeMetrics)
def get_approval_time_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return calculate_approval_times(db)

@router.get("/bottlenecks", response_model=BottleneckMetrics)
def get_bottleneck_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return calculate_bottlenecks(db)

@router.get("/completion-rate", response_model=CompletionRateMetrics)
def get_completion_rate_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return calculate_completion_rates(db)
