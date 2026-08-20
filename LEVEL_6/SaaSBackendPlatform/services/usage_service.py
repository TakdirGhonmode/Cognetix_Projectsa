from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from models.usage import UsageLog
from models.organization import Organization, OrganizationMember
from models.subscription import TenantSubscription
from schemas.usage import UsageStatsResponse, AnalyticsDashboardResponse

class UsageService:
    @staticmethod
    def log_request(db: Session, org_id: int, user_id: int, endpoint: str) -> UsageLog:
        log = UsageLog(
            organization_id=org_id,
            user_id=user_id,
            endpoint=endpoint
        )
        db.add(log)
        db.commit()
        return log

    @staticmethod
    def check_and_get_usage_stats(db: Session, org_id: int) -> UsageStatsResponse:
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

        tenant_sub = db.query(TenantSubscription).filter(
            TenantSubscription.organization_id == org_id,
            TenantSubscription.status == "active"
        ).first()

        plan_name = tenant_sub.plan.name if tenant_sub and tenant_sub.plan else "Free"
        max_daily_quota = tenant_sub.plan.max_api_calls_per_day if tenant_sub and tenant_sub.plan else 100
        max_members = tenant_sub.plan.max_users if tenant_sub and tenant_sub.plan else 3

        # Calculate API calls in the last 24 hours
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_api_calls = db.query(UsageLog).filter(
            UsageLog.organization_id == org_id,
            UsageLog.timestamp >= today_start
        ).count()

        member_count = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id
        ).count()

        used_pct = round((today_api_calls / max_daily_quota) * 100, 2) if max_daily_quota > 0 else 100.0

        alert_msg = None
        if used_pct >= 100.0:
            alert_msg = "ALERT: Daily API usage quota 100% exceeded! Requests may be rate-limited. Upgrade plan to increase limits."
        elif used_pct >= 80.0:
            alert_msg = f"WARNING: Daily API usage is at {used_pct}%. Consider upgrading to avoid disruption."

        return UsageStatsResponse(
            organization_id=org_id,
            organization_name=org.name,
            current_plan=plan_name,
            total_api_calls_today=today_api_calls,
            max_daily_quota=max_daily_quota,
            quota_used_percentage=used_pct,
            member_count=member_count,
            max_members_allowed=max_members,
            alert=alert_msg
        )

    @staticmethod
    def get_analytics_dashboard(db: Session, org_id: int) -> AnalyticsDashboardResponse:
        tenant_sub = db.query(TenantSubscription).filter(
            TenantSubscription.organization_id == org_id
        ).first()

        plan = tenant_sub.plan if tenant_sub else None
        plan_name = plan.name if plan else "Free"
        analytics_enabled = plan.has_analytics if plan else False

        # Usage last 30 days
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        total_30d = db.query(UsageLog).filter(
            UsageLog.organization_id == org_id,
            UsageLog.timestamp >= thirty_days_ago
        ).count()

        active_users = db.query(func.count(func.distinct(UsageLog.user_id))).filter(
            UsageLog.organization_id == org_id,
            UsageLog.timestamp >= thirty_days_ago
        ).scalar() or 0

        # Endpoint distribution
        endpoint_counts = db.query(
            UsageLog.endpoint, func.count(UsageLog.id)
        ).filter(
            UsageLog.organization_id == org_id,
            UsageLog.timestamp >= thirty_days_ago
        ).group_by(UsageLog.endpoint).all()

        endpoint_breakdown = {ep: count for ep, count in endpoint_counts}

        return AnalyticsDashboardResponse(
            organization_id=org_id,
            plan_name=plan_name,
            analytics_enabled=analytics_enabled,
            total_requests_30d=total_30d,
            active_users_count=active_users,
            metrics={
                "endpoint_breakdown": endpoint_breakdown,
                "health_status": "Healthy",
                "average_daily_calls": round(total_30d / 30, 2)
            }
        )
