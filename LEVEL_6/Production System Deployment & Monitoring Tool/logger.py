import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

# Ensure logs directory exists
LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOGS_DIR, "monitoring.log")

# Configure logger
logger = logging.getLogger("production_monitoring")
logger.setLevel(logging.INFO)

# Formatter
log_formatter = logging.Formatter(
    fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# File Handler (Max 10MB per file, up to 5 backups)
file_handler = RotatingFileHandler(
    LOG_FILE_PATH,
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8"
)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# Console Handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# Avoid duplicate handlers if reloaded
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def log_console_alert(message: str, severity: str = "WARNING", service_name: Optional[str] = None):
    """Logs an alert message both to console and monitoring.log with high visibility."""
    prefix = f"[ALERT - {severity}]"
    svc = f" [Service: {service_name}]" if service_name else ""
    full_msg = f"{prefix}{svc} {message}"
    
    if severity.upper() == "CRITICAL":
        logger.critical(full_msg)
    else:
        logger.warning(full_msg)


def record_audit_log(
    db: Session,
    action: str,
    entity_type: str,
    details: str,
    entity_id: Optional[int] = None,
    service_id: Optional[int] = None,
    event_type: str = "INFO"
) -> None:
    """
    Persists an immutable audit log record to MySQL audit_logs table and logs to file.
    """
    from models.models import AuditLog, utc_now

    try:
        audit_entry = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            service_id=service_id,
            details=details,
            event_type=event_type,
            timestamp=utc_now()
        )
        db.add(audit_entry)
        db.commit()
        logger.info(f"[AUDIT] Action={action} Entity={entity_type} ID={entity_id} Details={details}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to record audit log: {str(e)}")


def log_error_to_db(
    db: Session,
    error_message: str,
    severity: str = "ERROR",
    source: str = "APP_EXCEPTION",
    service_id: Optional[int] = None,
    stack_trace: Optional[str] = None
) -> None:
    """
    Persists an error record to the MySQL error_logs table and logs to file/console.
    """
    from models.models import ErrorLog, utc_now

    try:
        error_entry = ErrorLog(
            service_id=service_id,
            error_message=error_message,
            severity=severity,
            source=source,
            stack_trace=stack_trace,
            timestamp=utc_now()
        )
        db.add(error_entry)
        db.commit()
        logger.error(f"[ERROR-LOG] Source={source} ServiceID={service_id} Severity={severity} Error={error_message}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to persist error log: {str(e)}")
