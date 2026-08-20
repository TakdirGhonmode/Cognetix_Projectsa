import os
import sys
import time
import pytest
from fastapi.testclient import TestClient

# Ensure workspace is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from database import init_database, SessionLocal
from models.models import (
    Service,
    HealthCheck,
    ErrorLog,
    MonitoringRule,
    Alert,
    AuditLog,
    ServiceStatus,
    RuleType,
    AuditAction
)
from health_checker import perform_health_check
from alert_manager import evaluate_service_rules, resolve_alert
from report_generator import (
    calculate_service_metrics,
    generate_daily_report_data,
    generate_weekly_report_data,
    generate_comparison_report_data,
    export_report_to_json,
    export_report_to_csv,
    export_report_to_pdf
)

client = TestClient(app)


def setup_module(module):
    """Setup MySQL database tables before test execution."""
    init_database()


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"
    assert data["database"] == "MySQL"


def test_database_tables_exist():
    """Verify all 6 tables exist and can be queried."""
    db = SessionLocal()
    try:
        assert db.query(Service).count() >= 0
        assert db.query(HealthCheck).count() >= 0
        assert db.query(ErrorLog).count() >= 0
        assert db.query(MonitoringRule).count() >= 0
        assert db.query(Alert).count() >= 0
        assert db.query(AuditLog).count() >= 0
    finally:
        db.close()


def test_service_crud_and_configuration_auditing():
    """Test service registration, updates with audit actions, and retrieval."""
    test_svc_name = f"Test Service {int(time.time())}"
    
    # 1. Create Service
    create_payload = {
        "name": test_svc_name,
        "url": "https://httpbin.org/status/200",
        "check_interval_seconds": 60,
        "expected_status_code": 200,
        "timeout_seconds": 5,
        "is_active": True
    }
    res = client.post("/api/services", json=create_payload)
    assert res.status_code == 201
    svc_data = res.json()
    svc_id = svc_data["id"]
    assert svc_data["name"] == test_svc_name
    assert svc_data["current_status"] == "UNKNOWN"

    # Verify SERVICE_CREATED audit log
    db = SessionLocal()
    try:
        created_audit = db.query(AuditLog).filter(
            AuditLog.service_id == svc_id,
            AuditLog.action == AuditAction.SERVICE_CREATED.value
        ).first()
        assert created_audit is not None
        assert "Registered new service" in created_audit.details
    finally:
        db.close()

    # 2. Update Service Configuration
    update_payload = {
        "check_interval_seconds": 30,
        "timeout_seconds": 3,
        "expected_status_code": 201,
        "is_active": False
    }
    update_res = client.put(f"/api/services/{svc_id}", json=update_payload)
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["check_interval_seconds"] == 30
    assert updated["timeout_seconds"] == 3
    assert updated["expected_status_code"] == 201
    assert updated["is_active"] is False

    # Verify Configuration Audit Records
    db = SessionLocal()
    try:
        actions = [
            a.action for a in db.query(AuditLog).filter(AuditLog.service_id == svc_id).all()
        ]
        assert AuditAction.MONITORING_INTERVAL_UPDATED.value in actions
        assert AuditAction.TIMEOUT_UPDATED.value in actions
        assert AuditAction.EXPECTED_STATUS_UPDATED.value in actions
        assert AuditAction.SERVICE_DEACTIVATED.value in actions
    finally:
        db.close()

    # Re-activate service
    reactivate_res = client.put(f"/api/services/{svc_id}", json={"is_active": True, "expected_status_code": 200})
    assert reactivate_res.status_code == 200


def test_health_check_execution_and_error_logging():
    """Test health check execution on healthy and failing endpoints."""
    db = SessionLocal()
    try:
        # Create a service pointing to a non-existent domain to test DNS / Connection error handling
        failing_svc = Service(
            name=f"Failing Test Service {int(time.time())}",
            url="https://invalid-non-existent-monitoring-test-domain-12345.org",
            check_interval_seconds=60,
            expected_status_code=200,
            timeout_seconds=2,
            is_active=True
        )
        db.add(failing_svc)
        db.commit()
        db.refresh(failing_svc)
        failing_id = failing_svc.id

        # Perform health check
        check = perform_health_check(service=failing_svc, db=db)
        assert check.is_healthy is False
        assert check.error_message is not None
        assert failing_svc.consecutive_failures == 1
        assert failing_svc.current_status == "DEGRADED"

        # Verify ErrorLog record created
        err_log = db.query(ErrorLog).filter(ErrorLog.service_id == failing_id).first()
        assert err_log is not None
        assert err_log.source in ["DNS_ERROR", "CONNECTION_ERROR", "HTTP_TIMEOUT"]

        # Run 2 more checks to trigger consecutive failure >= 3 -> DOWN
        perform_health_check(service=failing_svc, db=db)
        perform_health_check(service=failing_svc, db=db)
        db.refresh(failing_svc)
        assert failing_svc.consecutive_failures == 3
        assert failing_svc.current_status == "DOWN"

    finally:
        db.close()


def test_monitoring_rules_and_alert_deduplication():
    """Test rule creation, evaluation PASS/FAIL audit logging, and alert deduplication."""
    db = SessionLocal()
    try:
        svc = Service(
            name=f"Rule Test Service {int(time.time())}",
            url="https://httpbin.org/status/200",
            check_interval_seconds=10,
            expected_status_code=200,
            timeout_seconds=5,
            consecutive_failures=3,
            current_status="DOWN",
            is_active=True
        )
        db.add(svc)
        db.commit()
        db.refresh(svc)

        # Create custom rule for this service
        rule = MonitoringRule(
            name="Test Consecutive Failure Rule",
            service_id=svc.id,
            rule_type=RuleType.CONSECUTIVE_FAILURES.value,
            threshold_value=2.0,
            time_window_minutes=60,
            is_enabled=True
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)

        # Mock latest health check
        fake_check = HealthCheck(
            service_id=svc.id,
            status_code=500,
            response_time_ms=120.0,
            is_healthy=False,
            error_message="Test failure"
        )
        db.add(fake_check)
        db.commit()

        # Evaluate rules -> Should trigger alert
        alerts1 = evaluate_service_rules(service=svc, latest_check=fake_check, db=db)
        assert len(alerts1) >= 1
        created_alert = alerts1[0]
        assert created_alert.is_resolved is False

        # Evaluate again -> Should deduplicate and not create a second active alert
        alerts2 = evaluate_service_rules(service=svc, latest_check=fake_check, db=db)
        assert len(alerts2) == 0

        # Verify audit logs contains RULE_EVALUATED
        eval_audits = db.query(AuditLog).filter(
            AuditLog.service_id == svc.id,
            AuditLog.action == AuditAction.RULE_EVALUATED.value
        ).all()
        assert len(eval_audits) >= 2

        # Resolve alert
        resolved = resolve_alert(db=db, alert_id=created_alert.id, resolution_notes="Resolved in unit test")
        assert resolved.is_resolved is True
        assert resolved.resolved_at is not None

    finally:
        db.close()


def test_metrics_api_and_uptime_formula():
    """Verify GET /api/metrics and Uptime % = (Healthy / Total) * 100."""
    res = client.get("/api/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "system_daily_uptime_percentage" in data
    assert "system_weekly_uptime_percentage" in data
    assert "services" in data
    assert len(data["services"]) >= 1

    svc_metrics = data["services"][0]
    assert "daily_uptime_percentage" in svc_metrics
    assert "weekly_uptime_percentage" in svc_metrics
    assert "weekly_breakdown" in svc_metrics


def test_reports_and_file_exports():
    """Verify daily/weekly/comparison reports and JSON/CSV/PDF file exports."""
    # Daily Report
    res_daily = client.get("/api/reports/daily")
    assert res_daily.status_code == 200
    assert res_daily.json()["report_type"] == "Daily System Health Report"

    # Weekly Report
    res_weekly = client.get("/api/reports/weekly")
    assert res_weekly.status_code == 200
    assert res_weekly.json()["report_type"] == "Weekly Monitoring Summary"

    # Compare Report
    res_comp = client.get("/api/reports/compare")
    assert res_comp.status_code == 200
    assert res_comp.json()["report_type"] == "Service Performance Comparison"

    # JSON Export
    res_json = client.get("/api/reports/export/json?report_type=daily")
    assert res_json.status_code == 200
    assert res_json.headers["content-type"] == "application/json"

    # CSV Export
    res_csv = client.get("/api/reports/export/csv?report_type=compare")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]

    # PDF Export
    res_pdf = client.get("/api/reports/export/pdf?report_type=weekly")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"


def test_logs_and_audits_endpoints():
    """Verify querying error logs and audit logs via API."""
    res_errors = client.get("/api/logs/errors?limit=10")
    assert res_errors.status_code == 200
    assert isinstance(res_errors.json(), list)

    res_audits = client.get("/api/logs/audit?limit=20")
    assert res_audits.status_code == 200
    assert isinstance(res_audits.json(), list)
    assert len(res_audits.json()) > 0
