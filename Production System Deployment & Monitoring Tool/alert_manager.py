import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.models import (
    Service,
    HealthCheck,
    MonitoringRule,
    Alert,
    ErrorLog,
    RuleType,
    AlertSeverity,
    AlertType,
    AuditAction,
    AuditEventType,
    utc_now
)
from logger import logger, log_console_alert, record_audit_log


def evaluate_service_rules(service: Service, latest_check: HealthCheck, db: Session) -> List[Alert]:
    """
    Evaluates all active rules applicable to the given service (both service-specific and global rules).
    Creates audit log records for both PASS and FAIL evaluations.
    Triggers deduplicated alerts when thresholds are breached.
    """
    rules = db.query(MonitoringRule).filter(
        MonitoringRule.is_enabled == True,
        (MonitoringRule.service_id == service.id) | (MonitoringRule.service_id == None)
    ).all()

    generated_alerts = []

    for rule in rules:
        is_breached = False
        breach_message = ""
        alert_type = AlertType.HEALTH_DEGRADED.value
        severity = AlertSeverity.WARNING.value
        metric_summary = ""

        try:
            if rule.rule_type == RuleType.RESPONSE_TIME.value:
                threshold_ms = float(rule.threshold_value)
                actual_latency_ms = latest_check.response_time_ms
                metric_summary = f"Actual={actual_latency_ms:.2f}ms, Threshold={threshold_ms:.2f}ms"

                if actual_latency_ms > threshold_ms:
                    is_breached = True
                    alert_type = AlertType.RESPONSE_TIME_EXCEEDED.value
                    severity = AlertSeverity.WARNING.value if actual_latency_ms < threshold_ms * 2 else AlertSeverity.CRITICAL.value
                    breach_message = (
                        f"Response time threshold breached for service '{service.name}'. "
                        f"Response time was {actual_latency_ms:.2f} ms (Threshold: {threshold_ms:.2f} ms)."
                    )

            elif rule.rule_type == RuleType.CONSECUTIVE_FAILURES.value:
                threshold_failures = int(rule.threshold_value)
                actual_failures = service.consecutive_failures
                metric_summary = f"Consecutive Failures={actual_failures}, Threshold={threshold_failures}"

                if actual_failures >= threshold_failures:
                    is_breached = True
                    alert_type = AlertType.SERVICE_DOWN.value
                    severity = AlertSeverity.CRITICAL.value
                    breach_message = (
                        f"Service '{service.name}' is DOWN! "
                        f"Consecutive failed checks reached {actual_failures} (Threshold: {threshold_failures})."
                    )

            elif rule.rule_type == RuleType.ERROR_FREQUENCY.value:
                window_mins = rule.time_window_minutes or 60
                threshold_errors = int(rule.threshold_value)
                window_start = utc_now() - timedelta(minutes=window_mins)

                error_count = db.query(func.count(ErrorLog.id)).filter(
                    ErrorLog.service_id == service.id,
                    ErrorLog.timestamp >= window_start
                ).scalar() or 0

                metric_summary = f"Errors in {window_mins}m={error_count}, Threshold={threshold_errors}"

                if error_count > threshold_errors:
                    is_breached = True
                    alert_type = AlertType.ERROR_RATE_EXCEEDED.value
                    severity = AlertSeverity.CRITICAL.value
                    breach_message = (
                        f"High error frequency detected for service '{service.name}'. "
                        f"{error_count} errors recorded in the past {window_mins} minutes (Threshold: {threshold_errors})."
                    )

            # Record audit log for PASS / FAIL
            evaluation_status = "FAIL" if is_breached else "PASS"
            audit_details = (
                f"Rule '{rule.name}' (ID: {rule.id}, Type: {rule.rule_type}) evaluation: {evaluation_status}. "
                f"Metrics: [{metric_summary}]."
            )
            record_audit_log(
                db=db,
                action=AuditAction.RULE_EVALUATED.value,
                entity_type="RULE",
                entity_id=rule.id,
                service_id=service.id,
                details=audit_details,
                event_type=AuditEventType.ALERT.value if is_breached else AuditEventType.AUDIT.value
            )

            # Handle Alert Triggering with Deduplication
            if is_breached:
                alert = trigger_alert(
                    db=db,
                    service=service,
                    rule=rule,
                    alert_type=alert_type,
                    severity=severity,
                    message=breach_message
                )
                if alert:
                    generated_alerts.append(alert)

        except Exception as e:
            logger.error(f"Error evaluating rule ID {rule.id} for service {service.id}: {str(e)}")

    return generated_alerts


def trigger_alert(
    db: Session,
    service: Service,
    rule: Optional[MonitoringRule],
    alert_type: str,
    severity: str,
    message: str
) -> Optional[Alert]:
    """
    Creates an alert record with deduplication.
    If an unresolved alert with the same service and alert_type already exists, duplicate firing is skipped.
    """
    try:
        existing_alert = db.query(Alert).filter(
            Alert.service_id == service.id,
            Alert.alert_type == alert_type,
            Alert.is_resolved == False
        ).first()

        if existing_alert:
            logger.info(
                f"[DEDUPLICATION] Active alert already exists for service '{service.name}' "
                f"(Alert ID: {existing_alert.id}, Type: {alert_type}). Skipping duplicate."
            )
            return None

        # 1. Create DB Alert Record
        alert = Alert(
            service_id=service.id,
            rule_id=rule.id if rule else None,
            alert_type=alert_type,
            severity=severity,
            message=message,
            is_resolved=False,
            triggered_at=utc_now()
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        # 2. Output to Console & File Logger
        log_console_alert(message=message, severity=severity, service_name=service.name)

        # 3. Create Audit Record
        record_audit_log(
            db=db,
            action=AuditAction.ALERT_TRIGGERED.value,
            entity_type="ALERT",
            entity_id=alert.id,
            service_id=service.id,
            details=f"Alert ID {alert.id} ({alert_type}) triggered: {message}",
            event_type=AuditEventType.ALERT.value
        )

        # 4. Optional Email Notification
        if os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true":
            send_email_alert(alert, service.name)

        return alert

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to trigger alert for service {service.name}: {str(e)}")
        return None


def resolve_alert(db: Session, alert_id: int, resolution_notes: Optional[str] = None) -> Optional[Alert]:
    """Marks an active alert as resolved and logs the resolution in audit_logs."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        return None

    if alert.is_resolved:
        return alert

    alert.is_resolved = True
    alert.resolved_at = utc_now()
    db.commit()
    db.refresh(alert)

    details = f"Alert ID {alert.id} ({alert.alert_type}) resolved."
    if resolution_notes:
        details += f" Resolution notes: {resolution_notes}"

    record_audit_log(
        db=db,
        action=AuditAction.ALERT_RESOLVED.value,
        entity_type="ALERT",
        entity_id=alert.id,
        service_id=alert.service_id,
        details=details,
        event_type=AuditEventType.AUDIT.value
    )
    logger.info(f"[ALERT RESOLVED] Alert ID {alert.id} marked as resolved.")
    return alert


def send_email_alert(alert: Alert, service_name: str):
    """Optional email alert dispatcher."""
    try:
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASSWORD")
        receiver = os.getenv("ALERT_RECEIVER_EMAIL")

        if not all([smtp_host, smtp_user, smtp_pass, receiver]):
            logger.warning("Email alerting enabled but SMTP configuration is incomplete.")
            return

        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = receiver
        msg["Subject"] = f"[MONITORING ALERT - {alert.severity}] Service: {service_name}"

        body = (
            f"ALERT DETAILS:\n"
            f"----------------------------------------\n"
            f"Service: {service_name}\n"
            f"Type: {alert.alert_type}\n"
            f"Severity: {alert.severity}\n"
            f"Triggered At: {alert.triggered_at} UTC\n"
            f"Message: {alert.message}\n"
        )
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        logger.info(f"Alert email sent successfully to {receiver}")
    except Exception as e:
        logger.error(f"Failed to send email alert: {str(e)}")
