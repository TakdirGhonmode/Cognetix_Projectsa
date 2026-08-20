from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.response_wrapper import StandardResponse
from schemas.billing import InvoiceResponse, WebhookEventRequest
from services.billing_service import BillingService
from auth.dependencies import get_current_active_user, require_role
from models.user import User

router = APIRouter(prefix="/api/v1/billing", tags=["Billing & Payments"])

@router.get("/invoices", response_model=StandardResponse[List[InvoiceResponse]])
def get_invoices(
    organization_id: int = Header(..., alias="X-Organization-ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _rbac: bool = Depends(require_role(["ADMIN", "ORG_OWNER"]))
):
    """
    Retrieve invoice history for an organization.
    Protected by RBAC: Requires ADMIN or ORG_OWNER role.
    """
    invoices = BillingService.get_org_invoices(db, organization_id)
    return StandardResponse(
        success=True,
        message="Billing invoices retrieved successfully",
        data=invoices
    )

@router.post("/webhook", response_model=StandardResponse[InvoiceResponse], status_code=status.HTTP_201_CREATED)
def stripe_webhook(
    webhook_data: WebhookEventRequest,
    db: Session = Depends(get_db)
):
    """
    Stripe payment gateway webhook handler simulation.
    Processes invoice payment status events (invoice.payment_succeeded, invoice.payment_failed).
    """
    invoice = BillingService.process_stripe_webhook(db, webhook_data)
    return StandardResponse(
        success=True,
        message="Payment webhook processed successfully",
        data=invoice
    )
