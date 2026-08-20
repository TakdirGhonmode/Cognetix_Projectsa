import os
from datetime import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from database import SessionLocal
from models.models import Service, AuditAction, AuditEventType, utc_now
from logger import logger, record_audit_log, log_error_to_db
from health_checker import perform_health_check

# Global background scheduler instance
scheduler = BackgroundScheduler()


def run_scheduled_health_checks():
    """
    Periodic job executed by APScheduler:
    1. Opens a dedicated DB session.
    2. Queries all active monitored services.
    3. Evaluates each service's individual check_interval_seconds against last_check_at.
    4. Executes health checks only for services whose interval has elapsed.
    5. Commits and cleans up DB session.
    """
    if SessionLocal is None:
        logger.warning("Database SessionLocal is not initialized. Skipping scheduled check cycle.")
        return

    db: Session = SessionLocal()
    try:
        now_utc = utc_now()
        active_services = db.query(Service).filter(Service.is_active == True).all()

        checked_count = 0
        for service in active_services:
            try:
                # Determine if check is due based on per-service check_interval_seconds
                is_due = False
                if service.last_check_at is None:
                    is_due = True
                else:
                    elapsed = (now_utc - service.last_check_at).total_seconds()
                    interval = service.check_interval_seconds if service.check_interval_seconds and service.check_interval_seconds > 0 else 60
                    if elapsed >= interval:
                        is_due = True

                if is_due:
                    perform_health_check(service=service, db=db)
                    checked_count += 1
            except Exception as item_err:
                logger.error(f"Error checking service ID {service.id} ({service.name}): {str(item_err)}")
                log_error_to_db(
                    db=db,
                    service_id=service.id,
                    error_message=f"Scheduler check failure: {str(item_err)}",
                    severity="ERROR",
                    source="SCHEDULER_ERROR"
                )

        logger.info(f"[SCHEDULER CYCLE] Completed evaluation: {checked_count}/{len(active_services)} active services checked.")
    except Exception as e:
        logger.error(f"Global error in scheduler cycle: {str(e)}")
    finally:
        db.close()


def start_scheduler(interval_seconds: int = 60):
    """Starts the background APScheduler monitoring cycle."""
    if not scheduler.running:
        scheduler.add_job(
            func=run_scheduled_health_checks,
            trigger=IntervalTrigger(seconds=interval_seconds),
            id="production_health_monitor_job",
            name="Periodic Service Health Monitor",
            replace_existing=True
        )
        scheduler.start()
        logger.info(f"APScheduler started successfully with base cycle of {interval_seconds}s.")

        # Record scheduler startup audit log
        if SessionLocal:
            db = SessionLocal()
            try:
                record_audit_log(
                    db=db,
                    action=AuditAction.SCHEDULER_STARTUP.value,
                    entity_type="SCHEDULER",
                    details=f"APScheduler monitoring engine started with cycle interval={interval_seconds}s.",
                    event_type=AuditEventType.AUDIT.value
                )
            finally:
                db.close()


def stop_scheduler():
    """Stops the APScheduler safely upon application shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped successfully.")

        # Record scheduler shutdown audit log
        if SessionLocal:
            db = SessionLocal()
            try:
                record_audit_log(
                    db=db,
                    action=AuditAction.SCHEDULER_SHUTDOWN.value,
                    entity_type="SCHEDULER",
                    details="APScheduler monitoring engine safely halted.",
                    event_type=AuditEventType.AUDIT.value
                )
            finally:
                db.close()
