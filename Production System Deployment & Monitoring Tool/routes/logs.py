from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models.models import ErrorLog, AuditLog, Service, ErrorLogResponse, AuditLogResponse

router = APIRouter(prefix="/api/logs", tags=["Logs & Audits"])


@router.get("/errors", response_model=List[ErrorLogResponse], summary="Query error logs")
def get_error_logs(
    service_id: Optional[int] = Query(None, description="Filter by service ID"),
    severity: Optional[str] = Query(None, description="Filter by severity: INFO, WARNING, ERROR, CRITICAL"),
    source: Optional[str] = Query(None, description="Filter by source"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Retrieves captured error and exception logs from MySQL."""
    query = db.query(ErrorLog, Service.name.label("service_name")).outerjoin(
        Service, ErrorLog.service_id == Service.id
    )

    if service_id is not None:
        query = query.filter(ErrorLog.service_id == service_id)
    if severity:
        query = query.filter(ErrorLog.severity == severity.upper())
    if source:
        query = query.filter(ErrorLog.source == source.upper())

    results = query.order_by(ErrorLog.timestamp.desc()).offset(skip).limit(limit).all()

    response = []
    for err, svc_name in results:
        response.append(ErrorLogResponse(
            id=err.id,
            service_id=err.service_id,
            service_name=svc_name,
            error_message=err.error_message,
            severity=err.severity,
            source=err.source,
            stack_trace=err.stack_trace,
            timestamp=err.timestamp
        ))
    return response


@router.get("/audit", response_model=List[AuditLogResponse], summary="Query immutable audit logs")
def get_audit_logs(
    service_id: Optional[int] = Query(None, description="Filter by service ID"),
    action: Optional[str] = Query(None, description="Filter by audit action"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type: SERVICE, RULE, ALERT, etc."),
    event_type: Optional[str] = Query(None, description="Filter by event type: INFO, AUDIT, ALERT, ERROR"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Retrieves operational audit logs for configuration changes, rule evaluations,
    health checks, alert triggers/resolutions, and scheduler lifecycle events.
    """
    query = db.query(AuditLog, Service.name.label("service_name")).outerjoin(
        Service, AuditLog.service_id == Service.id
    )

    if service_id is not None:
        query = query.filter(AuditLog.service_id == service_id)
    if action:
        query = query.filter(AuditLog.action == action.upper())
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type.upper())
    if event_type:
        query = query.filter(AuditLog.event_type == event_type.upper())

    results = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

    response = []
    for aud, svc_name in results:
        response.append(AuditLogResponse(
            id=aud.id,
            action=aud.action,
            entity_type=aud.entity_type,
            entity_id=aud.entity_id,
            service_id=aud.service_id,
            service_name=svc_name,
            details=aud.details,
            event_type=aud.event_type,
            timestamp=aud.timestamp
        ))
    return response
