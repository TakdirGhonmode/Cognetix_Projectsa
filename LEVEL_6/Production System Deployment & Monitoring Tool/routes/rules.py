from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.models import (
    MonitoringRule,
    RuleCreate,
    RuleUpdate,
    RuleResponse,
    AuditAction,
    AuditEventType
)
from logger import record_audit_log

router = APIRouter(prefix="/api/rules", tags=["Monitoring Rules"])


@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED, summary="Create a monitoring rule")
def create_rule(payload: RuleCreate, db: Session = Depends(get_db)):
    """
    Creates a new monitoring rule (global or service-specific):
    - Supported types: RESPONSE_TIME, CONSECUTIVE_FAILURES, ERROR_FREQUENCY.
    - Records RULE_CREATED in audit_logs.
    """
    rule = MonitoringRule(
        name=payload.name,
        service_id=payload.service_id,
        rule_type=payload.rule_type.value,
        threshold_value=payload.threshold_value,
        time_window_minutes=payload.time_window_minutes,
        is_enabled=payload.is_enabled
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    record_audit_log(
        db=db,
        action=AuditAction.RULE_CREATED.value,
        entity_type="RULE",
        entity_id=rule.id,
        service_id=rule.service_id,
        details=(
            f"Created monitoring rule '{rule.name}' (Type: {rule.rule_type}, "
            f"Threshold: {rule.threshold_value}, Window: {rule.time_window_minutes}m, "
            f"TargetService: {rule.service_id or 'GLOBAL'})."
        ),
        event_type=AuditEventType.AUDIT.value
    )

    return rule


@router.get("", response_model=List[RuleResponse], summary="List monitoring rules")
def list_rules(
    service_id: Optional[int] = Query(None, description="Filter by service ID"),
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled state"),
    rule_type: Optional[str] = Query(None, description="Filter by rule type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Lists monitoring rules with optional filtering."""
    query = db.query(MonitoringRule)
    if service_id is not None:
        query = query.filter(MonitoringRule.service_id == service_id)
    if is_enabled is not None:
        query = query.filter(MonitoringRule.is_enabled == is_enabled)
    if rule_type:
        query = query.filter(MonitoringRule.rule_type == rule_type.upper())
    return query.offset(skip).limit(limit).all()


@router.get("/{rule_id}", response_model=RuleResponse, summary="Get rule details")
def get_rule(rule_id: int, db: Session = Depends(get_db)):
    """Retrieves details of a specific monitoring rule."""
    rule = db.query(MonitoringRule).filter(MonitoringRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rule ID {rule_id} not found.")
    return rule


@router.put("/{rule_id}", response_model=RuleResponse, summary="Update monitoring rule")
def update_rule(rule_id: int, payload: RuleUpdate, db: Session = Depends(get_db)):
    """
    Updates rule parameters and logs specific configuration audit records:
    - RULE_THRESHOLD_UPDATED
    - RULE_TIME_WINDOW_UPDATED
    - RULE_ENABLED / RULE_DISABLED
    - RULE_UPDATED
    """
    rule = db.query(MonitoringRule).filter(MonitoringRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rule ID {rule_id} not found.")

    audit_records = []

    if payload.name is not None and payload.name != rule.name:
        audit_records.append((AuditAction.RULE_UPDATED.value, f"Name updated: '{rule.name}' -> '{payload.name}'"))
        rule.name = payload.name

    if payload.service_id is not None and payload.service_id != rule.service_id:
        audit_records.append((AuditAction.RULE_UPDATED.value, f"Target service changed from {rule.service_id} to {payload.service_id}"))
        rule.service_id = payload.service_id

    if payload.rule_type is not None and payload.rule_type.value != rule.rule_type:
        audit_records.append((AuditAction.RULE_UPDATED.value, f"Rule type changed: {rule.rule_type} -> {payload.rule_type.value}"))
        rule.rule_type = payload.rule_type.value

    if payload.threshold_value is not None and payload.threshold_value != rule.threshold_value:
        audit_records.append((
            AuditAction.RULE_THRESHOLD_UPDATED.value,
            f"Threshold value updated from {rule.threshold_value} to {payload.threshold_value}."
        ))
        rule.threshold_value = payload.threshold_value

    if payload.time_window_minutes is not None and payload.time_window_minutes != rule.time_window_minutes:
        audit_records.append((
            AuditAction.RULE_TIME_WINDOW_UPDATED.value,
            f"Time window updated from {rule.time_window_minutes}m to {payload.time_window_minutes}m."
        ))
        rule.time_window_minutes = payload.time_window_minutes

    if payload.is_enabled is not None and payload.is_enabled != rule.is_enabled:
        act = AuditAction.RULE_ENABLED.value if payload.is_enabled else AuditAction.RULE_DISABLED.value
        audit_records.append((act, f"Rule enabled state updated to {payload.is_enabled}."))
        rule.is_enabled = payload.is_enabled

    db.commit()
    db.refresh(rule)

    for act, detail in audit_records:
        record_audit_log(
            db=db,
            action=act,
            entity_type="RULE",
            entity_id=rule.id,
            service_id=rule.service_id,
            details=detail,
            event_type=AuditEventType.AUDIT.value
        )

    return rule


@router.patch("/{rule_id}/toggle", response_model=RuleResponse, summary="Toggle rule enabled/disabled state")
def toggle_rule(rule_id: int, db: Session = Depends(get_db)):
    """Toggles rule between active and inactive states."""
    rule = db.query(MonitoringRule).filter(MonitoringRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rule ID {rule_id} not found.")

    rule.is_enabled = not rule.is_enabled
    db.commit()
    db.refresh(rule)

    act = AuditAction.RULE_ENABLED.value if rule.is_enabled else AuditAction.RULE_DISABLED.value
    record_audit_log(
        db=db,
        action=act,
        entity_type="RULE",
        entity_id=rule.id,
        service_id=rule.service_id,
        details=f"Rule '{rule.name}' (ID: {rule.id}) toggled to enabled={rule.is_enabled}.",
        event_type=AuditEventType.AUDIT.value
    )

    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_200_OK, summary="Delete a monitoring rule")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    """Deletes a monitoring rule and records RULE_DELETED in audit_logs."""
    rule = db.query(MonitoringRule).filter(MonitoringRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rule ID {rule_id} not found.")

    rule_name = rule.name
    svc_id = rule.service_id
    db.delete(rule)
    db.commit()

    record_audit_log(
        db=db,
        action=AuditAction.RULE_DELETED.value,
        entity_type="RULE",
        entity_id=rule_id,
        service_id=svc_id,
        details=f"Deleted rule '{rule_name}' (ID: {rule_id}).",
        event_type=AuditEventType.AUDIT.value
    )

    return {"message": f"Rule '{rule_name}' (ID: {rule_id}) successfully deleted."}
