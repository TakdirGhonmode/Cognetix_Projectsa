from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.models import Alert, Service, AlertResponse, AlertResolveRequest
from alert_manager import resolve_alert

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.get("", response_model=List[AlertResponse], summary="List triggered alerts")
def list_alerts(
    service_id: Optional[int] = Query(None, description="Filter by service ID"),
    is_resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    severity: Optional[str] = Query(None, description="Filter by severity: WARNING, CRITICAL"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Lists alerts with filtering by resolution status, service, and severity."""
    query = db.query(Alert, Service.name.label("service_name")).join(Service, Alert.service_id == Service.id)

    if service_id is not None:
        query = query.filter(Alert.service_id == service_id)
    if is_resolved is not None:
        query = query.filter(Alert.is_resolved == is_resolved)
    if severity:
        query = query.filter(Alert.severity == severity.upper())

    results = query.order_by(Alert.triggered_at.desc()).offset(skip).limit(limit).all()

    response = []
    for alert, svc_name in results:
        resp = AlertResponse(
            id=alert.id,
            service_id=alert.service_id,
            service_name=svc_name,
            rule_id=alert.rule_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            message=alert.message,
            is_resolved=alert.is_resolved,
            triggered_at=alert.triggered_at,
            resolved_at=alert.resolved_at
        )
        response.append(resp)
    return response


@router.get("/{alert_id}", response_model=AlertResponse, summary="Get alert details")
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """Retrieves details of a specific alert."""
    result = db.query(Alert, Service.name.label("service_name")).join(
        Service, Alert.service_id == Service.id
    ).filter(Alert.id == alert_id).first()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert ID {alert_id} not found.")

    alert, svc_name = result
    return AlertResponse(
        id=alert.id,
        service_id=alert.service_id,
        service_name=svc_name,
        rule_id=alert.rule_id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        message=alert.message,
        is_resolved=alert.is_resolved,
        triggered_at=alert.triggered_at,
        resolved_at=alert.resolved_at
    )


@router.post("/{alert_id}/resolve", response_model=AlertResponse, summary="Resolve an active alert")
def resolve_alert_endpoint(
    alert_id: int,
    payload: AlertResolveRequest = None,
    db: Session = Depends(get_db)
):
    """
    Marks an active alert as resolved and records an audit log entry.
    """
    notes = payload.resolution_notes if payload else None
    resolved = resolve_alert(db=db, alert_id=alert_id, resolution_notes=notes)
    if not resolved:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert ID {alert_id} not found.")

    svc_name = resolved.service.name if resolved.service else "N/A"
    return AlertResponse(
        id=resolved.id,
        service_id=resolved.service_id,
        service_name=svc_name,
        rule_id=resolved.rule_id,
        alert_type=resolved.alert_type,
        severity=resolved.severity,
        message=resolved.message,
        is_resolved=resolved.is_resolved,
        triggered_at=resolved.triggered_at,
        resolved_at=resolved.resolved_at
    )
