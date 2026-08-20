from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.models import Service, ServiceMetrics, SystemMetricsSummary
from report_generator import calculate_service_metrics

router = APIRouter(prefix="/api/metrics", tags=["Performance Metrics"])


@router.get("", response_model=SystemMetricsSummary, summary="Get operational metrics across all services")
def get_all_metrics(db: Session = Depends(get_db)):
    """
    Returns operational uptime and performance metrics across all monitored services:
    - Daily uptime %
    - Weekly uptime %
    - 24h Error and Alert counts
    - Service breakdown
    """
    services = db.query(Service).all()
    metrics_list = [calculate_service_metrics(s, db, days=7) for s in services]

    total_services = len(services)
    active_count = sum(1 for s in services if s.is_active)
    healthy_count = sum(1 for s in services if s.current_status == "HEALTHY")
    degraded_count = sum(1 for s in services if s.current_status == "DEGRADED")
    down_count = sum(1 for s in services if s.current_status == "DOWN")

    avg_daily_uptime = round(sum(m.daily_uptime_percentage for m in metrics_list) / total_services, 2) if total_services > 0 else 100.0
    avg_weekly_uptime = round(sum(m.weekly_uptime_percentage for m in metrics_list) / total_services, 2) if total_services > 0 else 100.0
    total_errors = sum(m.error_count_24h for m in metrics_list)
    total_alerts = sum(m.alert_count_24h for m in metrics_list)

    return SystemMetricsSummary(
        total_services=total_services,
        active_services=active_count,
        healthy_services=healthy_count,
        degraded_services=degraded_count,
        down_services=down_count,
        system_daily_uptime_percentage=avg_daily_uptime,
        system_weekly_uptime_percentage=avg_weekly_uptime,
        total_errors_24h=total_errors,
        total_alerts_24h=total_alerts,
        services=metrics_list
    )


@router.get("/{service_id}", response_model=ServiceMetrics, summary="Get metrics for a specific service")
def get_service_metrics(service_id: int, db: Session = Depends(get_db)):
    """
    Returns detailed operational performance metrics for a specific service:
    - Daily uptime %
    - Weekly uptime %
    - 7-day daily breakdown
    - Average response time
    - Error and alert counts
    - Consecutive failure count
    """
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Service ID {service_id} not found.")

    return calculate_service_metrics(service=service, db=db, days=7)
