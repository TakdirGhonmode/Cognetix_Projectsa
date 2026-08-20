from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.models import Service, HealthCheck, HealthCheckResponse, ManualCheckResult
from health_checker import perform_health_check

router = APIRouter(prefix="/api/health", tags=["Health Monitoring"])


@router.get("/status", summary="Real-time status overview of all services")
def get_all_services_realtime_status(db: Session = Depends(get_db)):
    """Returns real-time status summary of all monitored services."""
    services = db.query(Service).all()
    results = []
    for s in services:
        results.append({
            "service_id": s.id,
            "name": s.name,
            "url": s.url,
            "current_status": s.current_status,
            "consecutive_failures": s.consecutive_failures,
            "is_active": s.is_active,
            "check_interval_seconds": s.check_interval_seconds,
            "last_check_at": s.last_check_at
        })
    return {
        "total_monitored": len(services),
        "healthy": sum(1 for s in services if s.current_status == "HEALTHY"),
        "degraded": sum(1 for s in services if s.current_status == "DEGRADED"),
        "down": sum(1 for s in services if s.current_status == "DOWN"),
        "services": results
    }


@router.post("/check/{service_id}", response_model=ManualCheckResult, summary="Trigger manual on-demand health check")
def trigger_manual_check(service_id: int, db: Session = Depends(get_db)):
    """
    Triggers an immediate on-demand HTTP health check for the specified service.
    Updates service status, stores health check & error logs, evaluates rules, and records audit.
    """
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Service ID {service_id} not found.")

    check = perform_health_check(service=service, db=db)

    return ManualCheckResult(
        service_id=service.id,
        service_name=service.name,
        url=service.url,
        status_code=check.status_code,
        response_time_ms=check.response_time_ms,
        is_healthy=check.is_healthy,
        error_message=check.error_message,
        current_status=service.current_status,
        checked_at=check.checked_at
    )


@router.get("/history/{service_id}", response_model=List[HealthCheckResponse], summary="Get health check history for a service")
def get_service_check_history(
    service_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Retrieves chronological health check history for a specific service."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Service ID {service_id} not found.")

    checks = db.query(HealthCheck).filter(
        HealthCheck.service_id == service_id
    ).order_by(HealthCheck.checked_at.desc()).offset(skip).limit(limit).all()

    return checks
