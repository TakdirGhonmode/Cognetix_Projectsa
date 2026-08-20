import logging
from database import engine, SessionLocal, Base
from models import User, WorkflowTemplate, WorkflowStage
from auth.security import get_password_hash
from workflow_engine import WorkflowEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_data")

def seed_database():
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if users exist
        existing_user = db.query(User).first()
        if existing_user:
            logger.info("Database already seeded. Skipping initial seeding.")
            return

        logger.info("Creating default enterprise demo users...")
        admin = User(username="admin", email="admin@enterprise.com", hashed_password=get_password_hash("AdminPass123!"), role="Admin", department="Executive")
        employee = User(username="john_employee", email="john@enterprise.com", hashed_password=get_password_hash("Pass123!"), role="Employee", department="Operations")
        hr_lead = User(username="hr_manager", email="hr@enterprise.com", hashed_password=get_password_hash("Pass123!"), role="HR_Approver", department="HR")
        fin_lead = User(username="finance_approver", email="finance@enterprise.com", hashed_password=get_password_hash("Pass123!"), role="Finance_Approver", department="Finance")
        proc_lead = User(username="procurement_lead", email="procurement@enterprise.com", hashed_password=get_password_hash("Pass123!"), role="Procurement_Officer", department="Procurement")
        comp_lead = User(username="compliance_head", email="compliance@enterprise.com", hashed_password=get_password_hash("Pass123!"), role="Compliance_Officer", department="Compliance")

        db.add_all([admin, employee, hr_lead, fin_lead, proc_lead, comp_lead])
        db.commit()

        logger.info("Creating default enterprise workflow templates...")
        
        # Template 1: Purchase Order Expense Approval
        po_template = WorkflowTemplate(
            name="Purchase Order Expense Approval",
            description="Multi-tier approval pipeline for procurement requests exceeding $5,000.",
            department="Procurement",
            created_by_id=admin.id,
            is_active=True
        )
        db.add(po_template)
        db.commit()
        db.refresh(po_template)

        stage1 = WorkflowStage(
            template_id=po_template.id,
            stage_order=1,
            name="Department Supervisor Approval",
            required_role="Employee",
            required_department="Operations",
            approval_required=True,
            sla_hours=12
        )
        stage2 = WorkflowStage(
            template_id=po_template.id,
            stage_order=2,
            name="Finance Budget Check & Release",
            required_role="Finance_Approver",
            required_department="Finance",
            approval_required=True,
            sla_hours=24
        )
        stage3 = WorkflowStage(
            template_id=po_template.id,
            stage_order=3,
            name="Procurement Purchase Order Fulfillment",
            required_role="Procurement_Officer",
            required_department="Procurement",
            approval_required=True,
            sla_hours=48
        )
        db.add_all([stage1, stage2, stage3])

        # Template 2: Enterprise Employee Onboarding
        hr_template = WorkflowTemplate(
            name="Enterprise Employee Onboarding",
            description="HR verification, background check, and IT provision pipeline.",
            department="HR",
            created_by_id=admin.id,
            is_active=True
        )
        db.add(hr_template)
        db.commit()
        db.refresh(hr_template)

        hr_stage1 = WorkflowStage(
            template_id=hr_template.id,
            stage_order=1,
            name="HR Credentials & Document Verification",
            required_role="HR_Approver",
            required_department="HR",
            approval_required=True,
            sla_hours=24
        )
        hr_stage2 = WorkflowStage(
            template_id=hr_template.id,
            stage_order=2,
            name="IT Equipment & Account Provisioning",
            required_role="Admin",
            required_department="Executive",
            approval_required=True,
            sla_hours=24
        )
        db.add_all([hr_stage1, hr_stage2])
        db.commit()

        logger.info("Initializing demo workflow instances and pending tasks...")
        inst1 = WorkflowEngine.start_workflow(
            db=db,
            template_id=po_template.id,
            title="PO-2026-9041: Cloud Server Upgrade ($12,500)",
            initiator=employee,
            payload_data={"amount": 12500, "vendor": "AWS Enterprise", "item": "EC2 Fleet Upgrade"}
        )

        inst2 = WorkflowEngine.start_workflow(
            db=db,
            template_id=hr_template.id,
            title="HR-2026-004: Senior Backend Engineer Onboarding (Jane Doe)",
            initiator=hr_lead,
            payload_data={"candidate": "Jane Doe", "position": "Senior Backend Engineer", "startDate": "2026-09-01"}
        )

        logger.info("Database seeding completed successfully!")

    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
