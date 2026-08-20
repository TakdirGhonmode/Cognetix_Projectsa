from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.models import (
    Service,
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    AuditAction,
    AuditEventType
)
from logger import record_audit_log, logger

router = APIRouter(prefix="/api/services", tags=["Services"])


@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED, summary="Register a new service")
def register_service(payload: ServiceCreate, db: Session = Depends(get_db)):
    """
    Registers a new service to be monitored:
    - Validates uniqueness of service name.
    - Sets initial status to UNKNOWN with 0 consecutive failures.
    - Records SERVICE_CREATED in audit_logs.
    """
    existing = db.query(Service).filter(Service.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Service with name '{payload.name}' is already registered."
        )

    service = Service(
        name=payload.name,
        url=payload.url,
        check_interval_seconds=payload.check_interval_seconds,
        expected_status_code=payload.expected_status_code,
        timeout_seconds=payload.timeout_seconds,
        is_active=payload.is_active
    )
    db.add(service)
    db.commit()
    db.refresh(service)

    # Configuration Audit Log
    record_audit_log(
        db=db,
        action=AuditAction.SERVICE_CREATED.value,
        entity_type="SERVICE",
        entity_id=service.id,
        service_id=service.id,
        details=(
            f"Registered new service '{service.name}'. URL={service.url}, "
            f"Interval={service.check_interval_seconds}s, Timeout={service.timeout_seconds}s, "
            f"ExpectedStatus={service.expected_status_code}, Active={service.is_active}"
        ),
        event_type=AuditEventType.AUDIT.value
    )

    return service


@router.get("", response_model=List[ServiceResponse], summary="List all monitored services")
def list_services(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    status_filter: Optional[str] = Query(None, description="Filter by status: HEALTHY, DEGRADED, DOWN, UNKNOWN"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Lists all monitored services with optional filtering."""
    query = db.query(Service)
    if is_active is not None:
        query = query.filter(Service.is_active == is_active)
    if status_filter:
        query = query.filter(Service.current_status == status_filter.upper())
    return query.offset(skip).limit(limit).all()


@router.get("/{service_id}", response_model=ServiceResponse, summary="Get service by ID")
def get_service(service_id: int, db: Session = Depends(get_db)):
    """Retrieves detailed information for a specific service."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Service ID {service_id} not found.")
    return service


@router.put("/{service_id}", response_model=ServiceResponse, summary="Update service configuration")
def update_service(service_id: int, payload: ServiceUpdate, db: Session = Depends(get_db)):
    """
    Updates service configuration and logs specific configuration audit records:
    - MONITORING_INTERVAL_UPDATED
    - TIMEOUT_UPDATED
    - EXPECTED_STATUS_UPDATED
    - SERVICE_ACTIVATED / SERVICE_DEACTIVATED
    - SERVICE_UPDATED
    """
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Service ID {service_id} not found.")

    audit_records = []

    if payload.name is not None and payload.name != service.name:
        existing = db.query(Service).filter(Service.name == payload.name, Service.id != service_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Service name '{payload.name}' already taken.")
        audit_records.append((AuditAction.SERVICE_UPDATED.value, f"Name changed: '{service.name}' -> '{payload.name}'"))
        service.name = payload.name

    if payload.url is not None and payload.url != service.url:
        audit_records.append((AuditAction.SERVICE_UPDATED.value, f"URL changed: '{service.url}' -> '{payload.url}'"))
        service.url = payload.url

    if payload.check_interval_seconds is not None and payload.check_interval_seconds != service.check_interval_seconds:
        audit_records.append((
            AuditAction.MONITORING_INTERVAL_UPDATED.value,
            f"Check interval updated from {service.check_interval_seconds}s to {payload.check_interval_seconds}s."
        ))
        service.check_interval_seconds = payload.check_interval_seconds

    if payload.timeout_seconds is not None and payload.timeout_seconds != service.timeout_seconds:
        audit_records.append((
            AuditAction.TIMEOUT_UPDATED.value,
            f"Timeout updated from {service.timeout_seconds}s to {payload.timeout_seconds}s."
        ))
        service.timeout_seconds = payload.timeout_seconds

    if payload.expected_status_code is not None and payload.expected_status_code != service.expected_status_code:
        audit_records.append((
            AuditAction.EXPECTED_STATUS_UPDATED.value,
            f"Expected status code updated from {service.expected_status_code} to {payload.expected_status_code}."
        ))
        service.expected_status_code = payload.expected_status_code

    if payload.is_active is not None and payload.is_active != service.is_active:
        action_name = AuditAction.SERVICE_ACTIVATED.value if payload.is_active else AuditAction.SERVICE_DEACTIVATED.value
        audit_records.append((
            action_name,
            f"Service active status updated to {payload.is_active}."
        ))
        service.is_active = payload.is_active

    db.commit()
    db.refresh(service)

    # Persist all individual configuration audit changes
    for act, detail in audit_records:
        record_audit_log(
            db=db,
            action=act,
            entity_type="SERVICE",
            entity_id=service.id,
            service_id=service.id,
            details=detail,
            event_type=AuditEventType.AUDIT.value
        )

    return service


@router.delete("/{service_id}", status_code=status.HTTP_200_OK, summary="Delete a monitored service")
def delete_service(service_id: int, db: Session = Depends(get_db)):
    """
    Deregisters a service and all its associated health checks and alerts.
    Logs SERVICE_DELETED in audit_logs.
    """
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Service ID {service_id} not found.")

    svc_name = service.name
    db.delete(service)
    db.commit()

    record_audit_log(
        db=db,
        action=AuditAction.SERVICE_DELETED.value,
        entity_type="SERVICE",
        entity_id=service_id,
        service_id=None,
        details=f"Deregistered and deleted service '{svc_name}' (ID: {service_id}).",
        event_type=AuditEventType.AUDIT.value
    )

    return {"message": f"Service '{svc_name}' (ID: {service_id}) successfully deleted."}
