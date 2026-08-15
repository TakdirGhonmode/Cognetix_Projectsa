import hashlib
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models.audit import AuditLog
from schemas.audit import AuditVerifyResponse

GENESIS_HASH = "0" * 64

def compute_audit_hash(
    previous_hash: str,
    instance_id: int,
    stage_id: int | None,
    actor_id: int,
    action: str,
    timestamp_iso: str,
    details: str | None
) -> str:
    stage_str = str(stage_id) if stage_id is not None else ""
    details_str = details if details is not None else ""
    raw_payload = f"{previous_hash}|{instance_id}|{stage_str}|{actor_id}|{action}|{timestamp_iso}|{details_str}"
    return hashlib.sha256(raw_payload.encode('utf-8')).hexdigest()

def log_audit_event(
    db: Session,
    instance_id: int,
    stage_id: int | None,
    actor_id: int,
    action: str,
    details: str | dict | None = None
) -> AuditLog:
    if isinstance(details, dict):
        details_str = json.dumps(details, sort_keys=True)
    else:
        details_str = str(details) if details is not None else ""

    # Get the last global audit log entry to form the chain
    last_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    previous_hash = last_log.current_hash if last_log and last_log.current_hash else GENESIS_HASH

    now_utc = datetime.now(timezone.utc)
    timestamp_iso = now_utc.isoformat()

    current_hash = compute_audit_hash(
        previous_hash=previous_hash,
        instance_id=instance_id,
        stage_id=stage_id,
        actor_id=actor_id,
        action=action,
        timestamp_iso=timestamp_iso,
        details=details_str
    )

    audit_entry = AuditLog(
        instance_id=instance_id,
        stage_id=stage_id,
        actor_id=actor_id,
        action=action,
        details=details_str,
        previous_hash=previous_hash,
        current_hash=current_hash,
        timestamp=now_utc
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    return audit_entry

def verify_audit_trail_integrity(db: Session) -> AuditVerifyResponse:
    logs = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
    if not logs:
        return AuditVerifyResponse(
            is_valid=True,
            total_records=0,
            corrupted_records=[],
            message="Audit log is empty. Integrity verified."
        )

    corrupted = []
    expected_previous_hash = GENESIS_HASH

    for log in logs:
        if log.previous_hash != expected_previous_hash:
            corrupted.append(log.id)

        # Re-compute hash using stored timestamp string
        ts_iso = log.timestamp.replace(tzinfo=timezone.utc).isoformat() if log.timestamp.tzinfo is None else log.timestamp.isoformat()
        
        # Verify hash match
        recalculated_hash = compute_audit_hash(
            previous_hash=log.previous_hash,
            instance_id=log.instance_id,
            stage_id=log.stage_id,
            actor_id=log.actor_id,
            action=log.action,
            timestamp_iso=ts_iso,
            details=log.details
        )

        if recalculated_hash != log.current_hash:
            if log.id not in corrupted:
                corrupted.append(log.id)

        expected_previous_hash = log.current_hash

    is_valid = len(corrupted) == 0
    message = "Audit trail is 100% tamper-free and verified." if is_valid else f"Audit trail tampered! Corrupted record IDs: {corrupted}"

    return AuditVerifyResponse(
        is_valid=is_valid,
        total_records=len(logs),
        corrupted_records=corrupted,
        message=message
    )
