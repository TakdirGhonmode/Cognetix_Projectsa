from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class InvoiceResponse(BaseModel):
    id: int
    organization_id: int
    amount: float
    currency: str
    status: str
    stripe_invoice_id: Optional[str] = None
    issued_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WebhookEventRequest(BaseModel):
    event_type: str  # invoice.payment_succeeded, invoice.payment_failed
    organization_id: int
    amount: float
    stripe_invoice_id: str
