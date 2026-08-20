import os
import sys
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from database import init_database, SessionLocal
from logger import logger, log_error_to_db, record_audit_log
from models.models import (
    MonitoringRule,
    RuleType,
    AuditAction,
    AuditEventType,
    utc_now
)
from scheduler import start_scheduler, stop_scheduler
from routes import (
    services_router,
    health_router,
    alerts_router,
    rules_router,
    metrics_router,
    reports_router,
    logs_router
)


def seed_default_monitoring_rules():
    """Seeds default threshold rules if no rules currently exist in MySQL."""
    if SessionLocal is None:
        return

    db = SessionLocal()
    try:
        count = db.query(MonitoringRule).count()
        if count == 0:
            default_rules = [
                MonitoringRule(
                    name="Global Response Time Limit (5000ms)",
                    service_id=None,
                    rule_type=RuleType.RESPONSE_TIME.value,
                    threshold_value=5000.0,
                    time_window_minutes=60,
                    is_enabled=True
                ),
                MonitoringRule(
                    name="Global Consecutive Downtime Limit (3 Checks)",
                    service_id=None,
                    rule_type=RuleType.CONSECUTIVE_FAILURES.value,
                    threshold_value=3.0,
                    time_window_minutes=60,
                    is_enabled=True
                ),
                MonitoringRule(
                    name="Global Error Frequency Threshold (10 errors/hour)",
                    service_id=None,
                    rule_type=RuleType.ERROR_FREQUENCY.value,
                    threshold_value=10.0,
                    time_window_minutes=60,
                    is_enabled=True
                )
            ]
            db.add_all(default_rules)
            db.commit()
            logger.info("Default global monitoring rules seeded successfully.")
    except Exception as e:
        db.rollback()
        logger.warning(f"Could not seed default rules: {str(e)}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Context Manager:
    - Startup: Initializes MySQL database, creates tables, seeds rules, starts scheduler.
    - Shutdown: Safely stops scheduler and releases resources.
    """
    logger.info("Starting Production System Deployment & Monitoring Tool...")

    # Ensure required directories exist
    os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "reports"), exist_ok=True)

    # 1. Initialize Database & Tables
    init_database()

    # 2. Seed Default Rules
    seed_default_monitoring_rules()

    # 3. Start APScheduler Background Engine
    scheduler_interval = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "60"))
    start_scheduler(interval_seconds=scheduler_interval)

    yield

    # Teardown
    logger.info("Shutting down Production System Deployment & Monitoring Tool...")
    stop_scheduler()


# Initialize FastAPI Application
app = FastAPI(
    title="Production System Deployment & Monitoring Tool",
    description="DevOps-grade API for continuous HTTP health checks, alert management, uptime tracking, and reporting.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catches all unhandled server exceptions:
    1. Persists stack trace and details into MySQL error_logs.
    2. Writes to monitoring.log and console.
    3. Records SYSTEM_EXCEPTION in audit_logs.
    4. Returns a safe HTTP 500 JSON without crashing the server.
    """
    stack_trace = traceback.format_exc()
    error_msg = f"Unhandled Exception on {request.method} {request.url.path}: {str(exc)}"
    logger.critical(f"[GLOBAL EXCEPTION] {error_msg}\n{stack_trace}")

    if SessionLocal:
        db = SessionLocal()
        try:
            log_error_to_db(
                db=db,
                error_message=error_msg,
                severity="CRITICAL",
                source="APP_EXCEPTION",
                stack_trace=stack_trace
            )
            record_audit_log(
                db=db,
                action=AuditAction.SYSTEM_EXCEPTION.value,
                entity_type="SYSTEM",
                details=error_msg,
                event_type=AuditEventType.ERROR.value
            )
        except Exception as db_err:
            logger.error(f"Failed to record exception in database: {str(db_err)}")
        finally:
            db.close()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "An internal server error occurred. The incident has been logged and audited.",
            "detail": str(exc),
            "timestamp": utc_now().isoformat() + "Z"
        }
    )


# Include API Routers
app.include_router(services_router)
app.include_router(health_router)
app.include_router(alerts_router)
app.include_router(rules_router)
app.include_router(metrics_router)
app.include_router(reports_router)
app.include_router(logs_router)


@app.get("/", summary="Root Health & Meta Information")
def root():
    """Root endpoint verifying that the monitoring engine is operational."""
    return {
        "system": "Production System Deployment & Monitoring Tool",
        "status": "OPERATIONAL",
        "timestamp": utc_now().isoformat() + "Z",
        "database": "MySQL",
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
