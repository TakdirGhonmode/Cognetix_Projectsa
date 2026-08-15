from fastapi import APIRouter, Depends, status, Header
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.response_wrapper import StandardResponse
from schemas.alert import AlertCreate, AlertResponse
from services.alert_service import AlertService
from auth.dependencies import get_current_active_user, require_role
from models.user import User

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])

@router.post("", response_model=StandardResponse[AlertResponse], status_code=status.HTTP_201_CREATED)
def create_alert(
    alert_data: AlertCreate,
    organization_id: int = Header(..., alias="X-Organization-ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _rbac: bool = Depends(require_role(["ADMIN", "ORG_OWNER", "MANAGER"]))
):
    """
    Generate a new system/quota alert for an organization.
    Protected by RBAC: Requires ADMIN, ORG_OWNER, or MANAGER role.
    Validates subscription tier alert limit before creating!
    """
    alert = AlertService.create_alert(db, organization_id, current_user.id, alert_data)
    return StandardResponse(
        success=True,
        message="Alert generated successfully",
        data=alert
    )

@router.get("", response_model=StandardResponse[List[AlertResponse]])
def get_alerts(
    organization_id: int = Header(..., alias="X-Organization-ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve all alerts generated for an organization.
    Requires user to be a member of the specified organization tenant.
    """
    alerts = AlertService.get_organization_alerts(db, organization_id, skip, limit)
    return StandardResponse(
        success=True,
        message="Alerts retrieved successfully",
        data=alerts
    )

@router.delete("/{alert_id}", response_model=StandardResponse[None])
def delete_alert(
    alert_id: int,
    organization_id: int = Header(..., alias="X-Organization-ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _rbac: bool = Depends(require_role(["ADMIN", "ORG_OWNER", "MANAGER"]))
):
    """
    Delete/dismiss a system alert by ID.
    Protected by RBAC: Requires ADMIN, ORG_OWNER, or MANAGER role.
    """
    AlertService.delete_alert(db, organization_id, alert_id)
    return StandardResponse(
        success=True,
        message="Alert deleted successfully",
        data=None
    )
