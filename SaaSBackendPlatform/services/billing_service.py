from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from models.billing import Invoice
from models.organization import Organization
from schemas.billing import WebhookEventRequest

class BillingService:
    @staticmethod
    def get_org_invoices(db: Session, org_id: int) -> List[Invoice]:
        return db.query(Invoice).filter(Invoice.organization_id == org_id).order_by(Invoice.issued_at.desc()).all()

    @staticmethod
    def process_stripe_webhook(db: Session, webhook_data: WebhookEventRequest) -> Invoice:
        org = db.query(Organization).filter(Organization.id == webhook_data.organization_id).first()
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target organization not found")

        status_str = "paid" if webhook_data.event_type == "invoice.payment_succeeded" else "failed"

        invoice = Invoice(
            organization_id=webhook_data.organization_id,
            amount=webhook_data.amount,
            currency="USD",
            status=status_str,
            stripe_invoice_id=webhook_data.stripe_invoice_id
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        return invoice
