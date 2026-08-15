from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class WorkflowInstance(Base):
    __tablename__ = "workflow_instances"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("workflow_templates.id"), nullable=False)
    title = Column(String(150), nullable=False)
    initiator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    current_stage_id = Column(Integer, ForeignKey("workflow_stages.id"), nullable=True)
    status = Column(String(50), nullable=False, default="PENDING", index=True) # PENDING, APPROVED, REJECTED, MODIFICATION_REQUESTED, COMPLETED
    payload = Column(Text, nullable=True)  # JSON formatted string
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    template = relationship("WorkflowTemplate", back_populates="instances")
    initiator = relationship("User", foreign_keys=[initiator_id], back_populates="initiated_workflows")
    current_stage = relationship("WorkflowStage", foreign_keys=[current_stage_id])
    tasks = relationship("TaskInstance", back_populates="instance", cascade="all, delete-orphan", order_by="TaskInstance.id")
    audit_logs = relationship("AuditLog", back_populates="instance", cascade="all, delete-orphan", order_by="AuditLog.id")


class TaskInstance(Base):
    __tablename__ = "task_instances"

    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(Integer, ForeignKey("workflow_instances.id"), nullable=False)
    stage_id = Column(Integer, ForeignKey("workflow_stages.id"), nullable=False)
    assigned_role = Column(String(50), nullable=True)
    assigned_department = Column(String(50), nullable=True)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(50), nullable=False, default="PENDING", index=True) # PENDING, APPROVED, REJECTED, MODIFICATION_REQUESTED
    decision_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    instance = relationship("WorkflowInstance", back_populates="tasks")
    stage = relationship("WorkflowStage", back_populates="task_instances")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id], back_populates="assigned_tasks")
