from database import SessionLocal, engine, Base
from models import (
    User,
    Organization,
    OrganizationMember,
    SubscriptionPlan,
    TenantSubscription,
    Alert,
    Invoice,
    UsageLog
)
from auth.security import get_password_hash

def seed_database():
    print("[+] Initializing Database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Subscription Plans
        print("[+] Seeding Subscription Plans...")
        plans_data = [
            {
                "name": "Free",
                "price_monthly": 0.0,
                "max_users": 3,
                "max_alerts": 10,
                "max_projects": 2,
                "max_api_calls_per_day": 100,
                "has_analytics": False,
                "has_export": False,
            },
            {
                "name": "Basic",
                "price_monthly": 29.99,
                "max_users": 10,
                "max_alerts": 100,
                "max_projects": 15,
                "max_api_calls_per_day": 1000,
                "has_analytics": True,
                "has_export": False,
            },
            {
                "name": "Premium",
                "price_monthly": 99.99,
                "max_users": 100,
                "max_alerts": 999999,
                "max_projects": 100,
                "max_api_calls_per_day": 100000,
                "has_analytics": True,
                "has_export": True,
            },
        ]

        plans_map = {}
        for p in plans_data:
            existing_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == p["name"]).first()
            if not existing_plan:
                plan = SubscriptionPlan(**p)
                db.add(plan)
                db.flush()
                plans_map[p["name"]] = plan
                print(f"   + Created Plan: {p['name']}")
            else:
                plans_map[p["name"]] = existing_plan
                print(f"   = Plan exists: {p['name']}")

        # 2. Seed Superadmin User
        print("[+] Seeding Superadmin User...")
        admin_email = "admin@saas.com"
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            admin = User(
                email=admin_email,
                hashed_password=get_password_hash("AdminPass123!"),
                full_name="System Superadmin",
                is_active=True,
                is_superadmin=True
            )
            db.add(admin)
            db.flush()
            print(f"   + Created Superadmin: {admin_email} (Password: AdminPass123!)")
        else:
            print(f"   = Superadmin exists: {admin_email}")

        # 3. Seed Sample Tenant Organization
        print("[+] Seeding Default Organization...")
        org_slug = "acme-corp"
        org = db.query(Organization).filter(Organization.slug == org_slug).first()
        if not org:
            org = Organization(
                name="Acme Corporation",
                slug=org_slug,
                owner_id=admin.id
            )
            db.add(org)
            db.flush()

            # Add Owner Member
            member = OrganizationMember(
                organization_id=org.id,
                user_id=admin.id,
                role="ORG_OWNER"
            )
            db.add(member)

            # Assign Free Plan
            sub = TenantSubscription(
                organization_id=org.id,
                plan_id=plans_map["Free"].id,
                status="active"
            )
            db.add(sub)

            # Add Initial Alert
            alert = Alert(
                organization_id=org.id,
                user_id=admin.id,
                title="System Initialized",
                message="Welcome to SaaS Backend Platform. Your Free subscription plan is active.",
                severity="INFO"
            )
            db.add(alert)
            print(f"   + Created Organization: Acme Corporation (Slug: acme-corp)")
        else:
            print(f"   = Organization exists: acme-corp")

        db.commit()
        print("[SUCCESS] Database Seeding Completed Successfully!")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error Seeding Database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
