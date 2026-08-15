from fastapi import APIRouter, Depends, Header, Response, status
from sqlalchemy.orm import Session
from database import get_db
from schemas.response_wrapper import StandardResponse
from schemas.usage import UsageStatsResponse, AnalyticsDashboardResponse
from services.usage_service import UsageService
from auth.dependencies import get_current_active_user, require_plan_feature
from models.user import User

router = APIRouter(tags=["Usage Tracking & Analytics"])

@router.get("/api/v1/usage", response_model=StandardResponse[UsageStatsResponse])
@router.get("/api/v1/usage/metrics", response_model=StandardResponse[UsageStatsResponse])
def get_usage_metrics(
    organization_id: int = Header(..., alias="X-Organization-ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve real-time API call metrics, daily quota usage percentage,
    member counts, and active alert notifications for the organization.
    """
    # Log usage for this request
    UsageService.log_request(db, organization_id, current_user.id, "/api/v1/usage")
    stats = UsageService.check_and_get_usage_stats(db, organization_id)
    return StandardResponse(
        success=True,
        message="Usage stats retrieved successfully",
        data=stats
    )

@router.get("/api/v1/analytics/dashboard", response_model=StandardResponse[AnalyticsDashboardResponse])
def get_analytics_dashboard(
    organization_id: int = Header(..., alias="X-Organization-ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _plan_check = Depends(require_plan_feature("has_analytics"))
):
    """
    Retrieve advanced analytics dashboard data.
    Feature-gated by subscription tier (Requires Basic or Premium plan).
    """
    UsageService.log_request(db, organization_id, current_user.id, "/api/v1/analytics/dashboard")
    dashboard = UsageService.get_analytics_dashboard(db, organization_id)
    return StandardResponse(
        success=True,
        message="Analytics dashboard data retrieved successfully",
        data=dashboard
    )

@router.get("/api/v1/analytics/export")
def export_usage_report_csv(
    organization_id: int = Header(..., alias="X-Organization-ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _plan_check = Depends(require_plan_feature("has_export"))
):
    """
    Export organization usage report as a CSV file download.
    Feature-gated by subscription tier (Requires Premium plan).
    """
    UsageService.log_request(db, organization_id, current_user.id, "/api/v1/analytics/export")
    stats = UsageService.check_and_get_usage_stats(db, organization_id)
    
    csv_content = f"Organization ID,Organization Name,Plan,Calls Today,Max Daily Quota,Quota Used %\n"
    csv_content += f"{stats.organization_id},{stats.organization_name},{stats.current_plan},{stats.total_api_calls_today},{stats.max_daily_quota},{stats.quota_used_percentage}%\n"
    
    headers = {"Content-Disposition": f"attachment; filename=usage_report_org_{organization_id}.csv"}
    return Response(content=csv_content, media_type="text/csv", headers=headers)
