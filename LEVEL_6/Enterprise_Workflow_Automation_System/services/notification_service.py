import logging
from typing import Dict, Any, Optional
from notifications.email import send_email_notification
from notifications.websocket import broadcast_websocket_event

logger = logging.getLogger("notification_service")

def dispatch_notification(
    event_name: str,
    recipient_email: Optional[str] = None,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None
):
    """Central dispatcher for enterprise workflow notifications, SLA breaches, and real-time updates."""
    logger.info(f"Dispatching notification event: '{event_name}'")
    if recipient_email and subject and body:
        send_email_notification(recipient_email, subject, body)
    if payload:
        broadcast_websocket_event(event_name, payload)
