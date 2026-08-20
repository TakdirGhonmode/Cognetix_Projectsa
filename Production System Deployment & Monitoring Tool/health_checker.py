import time
import socket
import traceback
from typing import Tuple, Optional
import requests
from sqlalchemy.orm import Session

from models.models import (
    Service,
    HealthCheck,
    ServiceStatus,
    ErrorSeverity,
    ErrorSource,
    AuditAction,
    AuditEventType,
    utc_now
)
from logger import logger, log_error_to_db, record_audit_log
from alert_manager import evaluate_service_rules


def perform_health_check(service: Service, db: Session) -> HealthCheck:
    """
    Executes a comprehensive health check against a registered service:
    1. Sends HTTP GET request with the service's configured timeout.
    2. Measures response latency in milliseconds.
    3. Validates HTTP status code against expected_status_code.
    4. Categorizes failure types (Timeout, DNS, SSL, Connection, Status mismatch, Unhandled).
    5. Updates service consecutive failures, downtime status, and last check timestamp.
    6. Persists HealthCheck record and ErrorLog if failed.
    7. Evaluates monitoring rules and triggers deduplicated alerts.
    """
    start_time = time.perf_counter()
    status_code: Optional[int] = None
    is_healthy = False
    error_message: Optional[str] = None
    error_source = ErrorSource.APP_EXCEPTION.value
    error_severity = ErrorSeverity.ERROR.value
    stack_trace: Optional[str] = None

    timeout = service.timeout_seconds if service.timeout_seconds and service.timeout_seconds > 0 else 5

    try:
        response = requests.get(
            service.url,
            timeout=timeout,
            headers={"User-Agent": "ProductionMonitoringTool/1.0"}
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        status_code = response.status_code

        expected_code = service.expected_status_code or 200
        if status_code == expected_code:
            is_healthy = True
        else:
            is_healthy = False
            error_source = ErrorSource.HTTP_STATUS_MISMATCH.value
            error_severity = ErrorSeverity.WARNING.value if status_code < 500 else ErrorSeverity.ERROR.value
            error_message = f"Expected status {expected_code}, received HTTP {status_code} ({response.reason})"

    except requests.exceptions.Timeout:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        is_healthy = False
        error_source = ErrorSource.HTTP_TIMEOUT.value
        error_severity = ErrorSeverity.ERROR.value
        error_message = f"Request timed out after {timeout} seconds."

    except requests.exceptions.SSLError as ssl_err:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        is_healthy = False
        error_source = ErrorSource.SSL_ERROR.value
        error_severity = ErrorSeverity.ERROR.value
        error_message = f"SSL Certificate verification failure: {str(ssl_err)}"
        stack_trace = traceback.format_exc()

    except requests.exceptions.ConnectionError as conn_err:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        is_healthy = False
        stack_trace = traceback.format_exc()
        
        # Determine if DNS failure or host unreachable
        if "getaddrinfo failed" in str(conn_err).lower() or isinstance(conn_err.args[0], socket.gaierror):
            error_source = ErrorSource.DNS_ERROR.value
            error_severity = ErrorSeverity.CRITICAL.value
            error_message = f"DNS resolution failed for hostname in URL '{service.url}'"
        else:
            error_source = ErrorSource.CONNECTION_ERROR.value
            error_severity = ErrorSeverity.CRITICAL.value
            error_message = f"Connection refused or server unreachable: {str(conn_err)}"

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        is_healthy = False
        error_source = ErrorSource.APP_EXCEPTION.value
        error_severity = ErrorSeverity.CRITICAL.value
        error_message = f"Unexpected health check exception: {str(exc)}"
        stack_trace = traceback.format_exc()

    # Update Service status and consecutive failures
    now_utc = utc_now()
    service.last_check_at = now_utc

    if is_healthy:
        service.consecutive_failures = 0
        service.current_status = ServiceStatus.HEALTHY.value
    else:
        service.consecutive_failures += 1
        if service.consecutive_failures >= 3:
            service.current_status = ServiceStatus.DOWN.value
        else:
            service.current_status = ServiceStatus.DEGRADED.value

    # 1. Persist Health Check Record
    health_check = HealthCheck(
        service_id=service.id,
        status_code=status_code,
        response_time_ms=round(elapsed_ms, 2),
        is_healthy=is_healthy,
        error_message=error_message,
        checked_at=now_utc
    )
    db.add(health_check)

    # 2. Persist Error Log if unhealthy
    if not is_healthy and error_message:
        log_error_to_db(
            db=db,
            service_id=service.id,
            error_message=error_message,
            severity=error_severity,
            source=error_source,
            stack_trace=stack_trace
        )

    # 3. Save database state
    db.commit()
    db.refresh(health_check)
    db.refresh(service)

    # 4. Audit Log
    check_details = (
        f"Health check for service '{service.name}' (ID: {service.id}) | "
        f"Healthy: {is_healthy} | Status: {status_code or 'N/A'} | "
        f"Latency: {elapsed_ms:.2f}ms | Consecutive Failures: {service.consecutive_failures}"
    )
    record_audit_log(
        db=db,
        action=AuditAction.HEALTH_CHECK_EXECUTED.value,
        entity_type="HEALTH_CHECK",
        entity_id=health_check.id,
        service_id=service.id,
        details=check_details,
        event_type=AuditEventType.INFO.value if is_healthy else AuditEventType.ALERT.value
    )

    # 5. Evaluate Rules & Thresholds
    evaluate_service_rules(service=service, latest_check=health_check, db=db)

    return health_check
