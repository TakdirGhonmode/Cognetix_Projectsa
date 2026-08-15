from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from models.subscription import SubscriptionPlan, TenantSubscription
from models.organization import OrganizationMember

class SubscriptionService:
    @staticmethod
    def list_plans(db: Session) -> List[SubscriptionPlan]:
        return db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).all()

    @staticmethod
    def get_tenant_subscription(db: Session, org_id: int) -> Optional[TenantSubscription]:
        return db.query(TenantSubscription).filter(
            TenantSubscription.organization_id == org_id
        ).first()

    @staticmethod
    def change_subscription(db: Session, org_id: int, target_plan_name: str) -> TenantSubscription:
        # Standardize plan name
        target_name = target_plan_name.strip().title()
        plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.name == target_name,
            SubscriptionPlan.is_active == True
        ).first()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription plan '{target_plan_name}' not found. Available plans: Free, Basic, Premium"
            )

        # Check existing member count for downgrade validation
        current_members_count = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id
        ).count()

        if current_members_count > plan.max_users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot downgrade to '{plan.name}' plan. Organization currently has {current_members_count} members, but '{plan.name}' plan permits a maximum of {plan.max_users} members."
            )

        sub = db.query(TenantSubscription).filter(
            TenantSubscription.organization_id == org_id
        ).first()

        if sub:
            sub.plan_id = plan.id
            sub.status = "active"
        else:
            sub = TenantSubscription(
                organization_id=org_id,
                plan_id=plan.id,
                status="active"
            )
            db.add(sub)

        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def cancel_subscription(db: Session, org_id: int) -> TenantSubscription:
        sub = db.query(TenantSubscription).filter(
            TenantSubscription.organization_id == org_id
        ).first()
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

        free_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == "Free").first()
        if free_plan:
            sub.plan_id = free_plan.id
        sub.status = "cancelled"
        
        db.commit()
        db.refresh(sub)
        return sub
