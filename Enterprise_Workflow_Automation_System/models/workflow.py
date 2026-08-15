from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    department = Column(String(50), nullable=False, default="General")
    is_active = Column(Boolean, default=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    stages = relationship("WorkflowStage", back_populates="template", cascade="all, delete-orphan", order_by="WorkflowStage.stage_order")
    instances = relationship("WorkflowInstance", back_populates="template")


class WorkflowStage(Base):
    __tablename__ = "workflow_stages"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("workflow_templates.id"), nullable=False)
    stage_order = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    required_role = Column(String(50), nullable=True)
    required_department = Column(String(50), nullable=True)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approval_required = Column(Boolean, default=True, nullable=False)
    sla_hours = Column(Integer, default=24, nullable=False)

    # Relationships
    template = relationship("WorkflowTemplate", back_populates="stages")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    task_instances = relationship("TaskInstance", back_populates="stage")
