from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Any
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text
)
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field

from database import Base


def utc_now():
    """Returns current UTC timestamp without timezone offset for naive MySQL DATETIME storage."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ============================================================================
# Enums
# ============================================================================

class ServiceStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"
    UNKNOWN = "UNKNOWN"


class RuleType(str, Enum):
    RESPONSE_TIME = "RESPONSE_TIME"
    CONSECUTIVE_FAILURES = "CONSECUTIVE_FAILURES"
    ERROR_FREQUENCY = "ERROR_FREQUENCY"


class AlertSeverity(str, Enum):
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertType(str, Enum):
    SERVICE_DOWN = "SERVICE_DOWN"
    RESPONSE_TIME_EXCEEDED = "RESPONSE_TIME_EXCEEDED"
    ERROR_RATE_EXCEEDED = "ERROR_RATE_EXCEEDED"
    HEALTH_DEGRADED = "HEALTH_DEGRADED"


class ErrorSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorSource(str, Enum):
    HTTP_TIMEOUT = "HTTP_TIMEOUT"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    DNS_ERROR = "DNS_ERROR"
    SSL_ERROR = "SSL_ERROR"
    HTTP_STATUS_MISMATCH = "HTTP_STATUS_MISMATCH"
    APP_EXCEPTION = "APP_EXCEPTION"
    SCHEDULER_ERROR = "SCHEDULER_ERROR"


class AuditEventType(str, Enum):
    INFO = "INFO"
    AUDIT = "AUDIT"
    ALERT = "ALERT"
    ERROR = "ERROR"


class AuditAction(str, Enum):
    SERVICE_CREATED = "SERVICE_CREATED"
    SERVICE_UPDATED = "SERVICE_UPDATED"
    MONITORING_INTERVAL_UPDATED = "MONITORING_INTERVAL_UPDATED"
    TIMEOUT_UPDATED = "TIMEOUT_UPDATED"
    EXPECTED_STATUS_UPDATED = "EXPECTED_STATUS_UPDATED"
    SERVICE_ACTIVATED = "SERVICE_ACTIVATED"
    SERVICE_DEACTIVATED = "SERVICE_DEACTIVATED"
    SERVICE_DELETED = "SERVICE_DELETED"
    RULE_CREATED = "RULE_CREATED"
    RULE_UPDATED = "RULE_UPDATED"
    RULE_THRESHOLD_UPDATED = "RULE_THRESHOLD_UPDATED"
    RULE_TIME_WINDOW_UPDATED = "RULE_TIME_WINDOW_UPDATED"
    RULE_ENABLED = "RULE_ENABLED"
    RULE_DISABLED = "RULE_DISABLED"
    RULE_DELETED = "RULE_DELETED"
    RULE_EVALUATED = "RULE_EVALUATED"
    ALERT_TRIGGERED = "ALERT_TRIGGERED"
    ALERT_RESOLVED = "ALERT_RESOLVED"
    HEALTH_CHECK_EXECUTED = "HEALTH_CHECK_EXECUTED"
    SCHEDULER_STARTUP = "SCHEDULER_STARTUP"
    SCHEDULER_SHUTDOWN = "SCHEDULER_SHUTDOWN"
    SYSTEM_EXCEPTION = "SYSTEM_EXCEPTION"


# ============================================================================
# SQLAlchemy ORM Models
# ============================================================================

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    url = Column(String(255), nullable=False)
    check_interval_seconds = Column(Integer, default=60, nullable=False)
    expected_status_code = Column(Integer, default=200, nullable=False)
    timeout_seconds = Column(Integer, default=5, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    consecutive_failures = Column(Integer, default=0, nullable=False)
    current_status = Column(String(20), default=ServiceStatus.UNKNOWN.value, nullable=False)
    last_check_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    health_checks = relationship("HealthCheck", back_populates="service", cascade="all, delete-orphan")
    error_logs = relationship("ErrorLog", back_populates="service")
    alerts = relationship("Alert", back_populates="service", cascade="all, delete-orphan")
    rules = relationship("MonitoringRule", back_populates="service", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="service")


class HealthCheck(Base):
    __tablename__ = "health_checks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Float, nullable=False)
    is_healthy = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    checked_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    # Relationships
    service = relationship("Service", back_populates="health_checks")


class ErrorLog(Base):
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="SET NULL"), nullable=True, index=True)
    error_message = Column(Text, nullable=False)
    severity = Column(String(20), default=ErrorSeverity.ERROR.value, nullable=False)
    source = Column(String(100), nullable=False)
    stack_trace = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)

    # Relationships
    service = relationship("Service", back_populates="error_logs")


class MonitoringRule(Base):
    __tablename__ = "monitoring_rules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=True, index=True)
    rule_type = Column(String(50), nullable=False)  # RESPONSE_TIME, CONSECUTIVE_FAILURES, ERROR_FREQUENCY
    threshold_value = Column(Float, nullable=False)  # e.g. 5000 (ms), 3 (failures), 10 (errors)
    time_window_minutes = Column(Integer, default=60, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    service = relationship("Service", back_populates="rules")
    alerts = relationship("Alert", back_populates="rule")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(Integer, ForeignKey("monitoring_rules.id", ondelete="SET NULL"), nullable=True, index=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), default=AlertSeverity.WARNING.value, nullable=False)
    message = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False, index=True)
    triggered_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    service = relationship("Service", back_populates="alerts")
    rule = relationship("MonitoringRule", back_populates="alerts")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="SET NULL"), nullable=True, index=True)
    details = Column(Text, nullable=False)
    event_type = Column(String(20), default=AuditEventType.INFO.value, nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)

    # Relationships
    service = relationship("Service", back_populates="audit_logs")


# ============================================================================
# Pydantic Schemas
# ============================================================================

# Service Schemas
class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, json_schema_extra={"example": "Payment Gateway"})
    url: str = Field(..., json_schema_extra={"example": "https://httpbin.org/status/200"})
    check_interval_seconds: int = Field(60, ge=5, le=86400, json_schema_extra={"example": 60})
    expected_status_code: int = Field(200, ge=100, le=599, json_schema_extra={"example": 200})
    timeout_seconds: int = Field(5, ge=1, le=60, json_schema_extra={"example": 5})
    is_active: bool = Field(True, json_schema_extra={"example": True})


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    url: Optional[str] = None
    check_interval_seconds: Optional[int] = Field(None, ge=5, le=86400)
    expected_status_code: Optional[int] = Field(None, ge=100, le=599)
    timeout_seconds: Optional[int] = Field(None, ge=1, le=60)
    is_active: Optional[bool] = None


class ServiceResponse(ServiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    consecutive_failures: int
    current_status: str
    last_check_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# Health Check Schemas
class HealthCheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    status_code: Optional[int]
    response_time_ms: float
    is_healthy: bool
    error_message: Optional[str]
    checked_at: datetime


class ManualCheckResult(BaseModel):
    service_id: int
    service_name: str
    url: str
    status_code: Optional[int]
    response_time_ms: float
    is_healthy: bool
    error_message: Optional[str]
    current_status: str
    checked_at: datetime


# Monitoring Rule Schemas
class RuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, json_schema_extra={"example": "High Latency Threshold"})
    service_id: Optional[int] = Field(None, description="Null for global rule", json_schema_extra={"example": 1})
    rule_type: RuleType = Field(..., json_schema_extra={"example": RuleType.RESPONSE_TIME})
    threshold_value: float = Field(..., gt=0, description="e.g., ms for latency, count for failures/errors", json_schema_extra={"example": 5000.0})
    time_window_minutes: int = Field(60, ge=1, le=1440, json_schema_extra={"example": 60})
    is_enabled: bool = Field(True, json_schema_extra={"example": True})


class RuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    service_id: Optional[int] = None
    rule_type: Optional[RuleType] = None
    threshold_value: Optional[float] = Field(None, gt=0)
    time_window_minutes: Optional[int] = Field(None, ge=1, le=1440)
    is_enabled: Optional[bool] = None


class RuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    service_id: Optional[int]
    rule_type: str
    threshold_value: float
    time_window_minutes: int
    is_enabled: bool
    created_at: datetime
    updated_at: datetime


# Alert Schemas
class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    service_name: Optional[str] = None
    rule_id: Optional[int]
    alert_type: str
    severity: str
    message: str
    is_resolved: bool
    triggered_at: datetime
    resolved_at: Optional[datetime] = None


class AlertResolveRequest(BaseModel):
    resolution_notes: Optional[str] = Field(None, json_schema_extra={"example": "Service issue investigated and resolved."})


# Error & Audit Log Schemas
class ErrorLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: Optional[int]
    service_name: Optional[str] = None
    error_message: str
    severity: str
    source: str
    stack_trace: Optional[str]
    timestamp: datetime


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    entity_type: str
    entity_id: Optional[int]
    service_id: Optional[int]
    service_name: Optional[str] = None
    details: str
    event_type: str
    timestamp: datetime


# Metrics & Report Schemas
class DailyBreakdown(BaseModel):
    date: str
    total_checks: int
    healthy_checks: int
    uptime_percentage: float
    avg_response_time_ms: float
    error_count: int


class ServiceMetrics(BaseModel):
    service_id: int
    service_name: str
    url: str
    current_status: str
    daily_uptime_percentage: float
    weekly_uptime_percentage: float
    avg_response_time_ms: float
    total_checks_24h: int
    healthy_checks_24h: int
    error_count_24h: int
    alert_count_24h: int
    active_alerts_count: int
    consecutive_failures: int
    weekly_breakdown: List[DailyBreakdown] = []


class SystemMetricsSummary(BaseModel):
    total_services: int
    active_services: int
    healthy_services: int
    degraded_services: int
    down_services: int
    system_daily_uptime_percentage: float
    system_weekly_uptime_percentage: float
    total_errors_24h: int
    total_alerts_24h: int
    services: List[ServiceMetrics]
