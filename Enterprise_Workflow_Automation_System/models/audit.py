from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(Integer, ForeignKey("workflow_instances.id"), nullable=False)
    stage_id = Column(Integer, ForeignKey("workflow_stages.id"), nullable=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)
    details = Column(Text, nullable=True)
    previous_hash = Column(String(64), nullable=False, default="0" * 64)
    current_hash = Column(String(64), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    instance = relationship("WorkflowInstance", back_populates="audit_logs")
    stage = relationship("WorkflowStage", foreign_keys=[stage_id])
    actor = relationship("User", foreign_keys=[actor_id], back_populates="audit_logs")
