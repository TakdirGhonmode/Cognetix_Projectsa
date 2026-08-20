from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # e.g., Free, Basic, Premium
    price_monthly = Column(Float, default=0.0)
    max_users = Column(Integer, default=3)
    max_alerts = Column(Integer, default=10)
    max_projects = Column(Integer, default=2)
    max_api_calls_per_day = Column(Integer, default=100)
    has_analytics = Column(Boolean, default=False)
    has_export = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    tenant_subscriptions = relationship("TenantSubscription", back_populates="plan")

class TenantSubscription(Base):
    __tablename__ = "tenant_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), unique=True, nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    status = Column(String(50), default="active")  # active, cancelled, past_due
    start_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_date = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, default=True)

    organization = relationship("Organization", back_populates="subscription")
    plan = relationship("SubscriptionPlan", back_populates="tenant_subscriptions")
