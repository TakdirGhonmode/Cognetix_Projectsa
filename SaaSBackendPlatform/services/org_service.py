from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from models.user import User
from models.organization import Organization, OrganizationMember
from models.subscription import SubscriptionPlan, TenantSubscription
from schemas.organization import OrganizationCreate, MemberAdd, MemberResponse

class OrgService:
    @staticmethod
    def create_organization(db: Session, org_data: OrganizationCreate, owner: User) -> Organization:
        existing_slug = db.query(Organization).filter(Organization.slug == org_data.slug).first()
        if existing_slug:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Organization slug '{org_data.slug}' is already taken"
            )

        org = Organization(
            name=org_data.name,
            slug=org_data.slug,
            owner_id=owner.id
        )
        db.add(org)
        db.flush()

        # Add owner as ORG_OWNER member
        member = OrganizationMember(
            organization_id=org.id,
            user_id=owner.id,
            role="ORG_OWNER"
        )
        db.add(member)

        # Attach default 'Free' subscription plan
        free_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == "Free").first()
        if not free_plan:
            # Fallback if seed script hasn't run
            free_plan = SubscriptionPlan(
                name="Free",
                price_monthly=0.0,
                max_users=3,
                max_projects=2,
                max_api_calls_per_day=100,
                has_analytics=False,
                has_export=False
            )
            db.add(free_plan)
            db.flush()

        sub = TenantSubscription(
            organization_id=org.id,
            plan_id=free_plan.id,
            status="active"
        )
        db.add(sub)

        db.commit()
        db.refresh(org)
        return org

    @staticmethod
    def get_user_organizations(db: Session, user_id: int) -> List[Organization]:
        memberships = db.query(OrganizationMember).filter(OrganizationMember.user_id == user_id).all()
        org_ids = [m.organization_id for m in memberships]
        return db.query(Organization).filter(Organization.id.in_(org_ids)).all()

    @staticmethod
    def get_organization_by_id(db: Session, org_id: int) -> Optional[Organization]:
        return db.query(Organization).filter(Organization.id == org_id).first()

    @staticmethod
    def add_member(db: Session, org_id: int, member_data: MemberAdd) -> MemberResponse:
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

        # Subscription limit enforcement: check current member count vs plan max_users limit
        current_members_count = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id
        ).count()

        tenant_sub = db.query(TenantSubscription).filter(
            TenantSubscription.organization_id == org_id,
            TenantSubscription.status == "active"
        ).first()

        max_allowed = tenant_sub.plan.max_users if tenant_sub and tenant_sub.plan else 3

        if current_members_count >= max_allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subscription limit reached ({current_members_count}/{max_allowed} users). Please upgrade your subscription plan to add more members."
            )

        # Find user to add
        target_user = db.query(User).filter(User.email == member_data.email).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email '{member_data.email}' not found. User must register before being added to an organization."
            )

        existing_member = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == target_user.id
        ).first()

        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this organization"
            )

        new_member = OrganizationMember(
            organization_id=org_id,
            user_id=target_user.id,
            role=member_data.role.upper()
        )
        db.add(new_member)
        db.commit()
        db.refresh(new_member)

        return MemberResponse(
            id=new_member.id,
            user_id=target_user.id,
            email=target_user.email,
            full_name=target_user.full_name,
            role=new_member.role,
            joined_at=new_member.joined_at
        )

    @staticmethod
    def get_members(db: Session, org_id: int) -> List[MemberResponse]:
        memberships = db.query(OrganizationMember).filter(OrganizationMember.organization_id == org_id).all()
        res = []
        for m in memberships:
            res.append(MemberResponse(
                id=m.id,
                user_id=m.user_id,
                email=m.user.email,
                full_name=m.user.full_name,
                role=m.role,
                joined_at=m.joined_at
            ))
        return res

    @staticmethod
    def remove_member(db: Session, org_id: int, user_id: int) -> bool:
        member = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id
        ).first()
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found in organization")
        
        db.delete(member)
        db.commit()
        return True
