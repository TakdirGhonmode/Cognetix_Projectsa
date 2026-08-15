import logging

logger = logging.getLogger("notifications.email")

def send_email_notification(recipient_email: str, subject: str, message: str) -> bool:
    """Email notification provider stub for enterprise expansion."""
    logger.info(f"[EMAIL NOTIFICATION STUB] To: {recipient_email} | Subject: '{subject}' | Message: {message}")
    return True
