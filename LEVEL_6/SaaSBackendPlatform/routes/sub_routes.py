from fastapi import APIRouter, Depends, status, Header
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.response_wrapper import StandardResponse
from schemas.subscription import SubscriptionPlanResponse, TenantSubscriptionResponse, ChangePlanRequest
from services.subscription_service import SubscriptionService
from auth.dependencies import get_current_active_user, require_role
from models.user import User

router = APIRouter(prefix="/api/v1/subscriptions", tags=["Subscriptions"])

@router.get("", response_model=StandardResponse[List[SubscriptionPlanResponse]])
@router.get("/plans", response_model=StandardResponse[List[SubscriptionPlanResponse]])
def list_subscription_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all available subscription plans (Free, Basic, Premium)."""
    plans = SubscriptionService.list_plans(db)
    return StandardResponse(
        success=True,
        message="Subscription plans fetched successfully",
        data=plans
    )

@router.get("/current", response_model=StandardResponse[TenantSubscriptionResponse])
def get_current_subscription(
    organization_id: int = Header(..., alias="X-Organization-ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve active subscription for tenant organization."""
    sub = SubscriptionService.get_tenant_subscription(db, organization_id)
    return StandardResponse(
        success=True,
        message="Tenant subscription retrieved successfully",
        data=sub
    )

@router.post("/assign", response_model=StandardResponse[TenantSubscriptionResponse])
@router.post("/change-plan", response_model=StandardResponse[TenantSubscriptionResponse])
def change_subscription_plan(
    req: ChangePlanRequest,
    organization_id: int = Header(..., alias="X-Organization-ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _rbac: bool = Depends(require_role(["ADMIN", "ORG_OWNER"]))
):
    """
    Assign or change subscription plan (Upgrade / Downgrade).
    Protected by RBAC: Requires ADMIN or ORG_OWNER role.
    Validates member count limits before permitting plan downgrade!
    """
    sub = SubscriptionService.change_subscription(db, organization_id, req.plan_name)
    return StandardResponse(
        success=True,
        message=f"Subscription plan updated successfully to '{req.plan_name.title()}'",
        data=sub
    )

@router.post("/cancel", response_model=StandardResponse[TenantSubscriptionResponse])
def cancel_subscription(
    organization_id: int = Header(..., alias="X-Organization-ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _rbac: bool = Depends(require_role(["ADMIN", "ORG_OWNER"]))
):
    """
    Cancel subscription and revert tenant to Free plan tier.
    Protected by RBAC: Requires ADMIN or ORG_OWNER role.
    """
    sub = SubscriptionService.cancel_subscription(db, organization_id)
    return StandardResponse(
        success=True,
        message="Subscription cancelled successfully",
        data=sub
    )
