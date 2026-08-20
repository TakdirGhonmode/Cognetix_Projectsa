from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.user import User
from models.audit import AuditLog
from schemas.audit import AuditLogResponse, AuditVerifyResponse
from auth.rbac import get_current_active_user
from services.audit_service import verify_audit_trail_integrity

router = APIRouter(prefix="/audit", tags=["Audit Trail Management"])

@router.get("", response_model=List[AuditLogResponse])
def get_audit_logs(
    instance_id: Optional[int] = Query(None, description="Filter by workflow instance ID"),
    actor_id: Optional[int] = Query(None, description="Filter by actor user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(AuditLog)
    if instance_id is not None:
        query = query.filter(AuditLog.instance_id == instance_id)
    if actor_id is not None:
        query = query.filter(AuditLog.actor_id == actor_id)
    if action is not None:
        query = query.filter(AuditLog.action == action)
    return query.order_by(AuditLog.id.desc()).all()

@router.get("/verify", response_model=AuditVerifyResponse)
def verify_audit_integrity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return verify_audit_trail_integrity(db)
