from models.user import User
from models.workflow import WorkflowTemplate, WorkflowStage
from workflow_engine import WorkflowEngine
from auth.security import get_password_hash

def test_workflow_lifecycle_approval(db_session):
    # Setup test users
    initiator = User(username="init_user", email="init@test.com", hashed_password=get_password_hash("pass"), role="Employee", department="Operations")
    approver1 = User(username="mgr_user", email="mgr@test.com", hashed_password=get_password_hash("pass"), role="Manager", department="Operations")
    approver2 = User(username="fin_user", email="fin@test.com", hashed_password=get_password_hash("pass"), role="Finance_Approver", department="Finance")
    db_session.add_all([initiator, approver1, approver2])
    db_session.commit()

    # Create Template
    tpl = WorkflowTemplate(name="Test PO", description="PO Workflow", department="Finance", is_active=True)
    db_session.add(tpl)
    db_session.commit()

    stg1 = WorkflowStage(template_id=tpl.id, stage_order=1, name="Manager Stage", required_role="Manager", approval_required=True, sla_hours=12)
    stg2 = WorkflowStage(template_id=tpl.id, stage_order=2, name="Finance Stage", required_role="Finance_Approver", approval_required=True, sla_hours=24)
    db_session.add_all([stg1, stg2])
    db_session.commit()

    # Start Workflow
    inst = WorkflowEngine.start_workflow(db_session, tpl.id, "PO-101", initiator, {"amount": 5000})
    assert inst.status == "PENDING"
    assert inst.current_stage_id == stg1.id
    assert len(inst.tasks) == 1
    task1 = inst.tasks[0]
    assert task1.status == "PENDING"

    # Approve Stage 1
    inst = WorkflowEngine.approve_task(db_session, task1.id, approver1, "Manager approved")
    assert inst.current_stage_id == stg2.id
    assert len(inst.tasks) == 2
    task2 = inst.tasks[1]
    assert task2.status == "PENDING"

    # Approve Stage 2 (Final)
    inst = WorkflowEngine.approve_task(db_session, task2.id, approver2, "Finance approved")
    assert inst.status == "COMPLETED"
    assert inst.current_stage_id is None
    assert inst.completed_at is not None

def test_workflow_rejection_routing(db_session):
    initiator = User(username="init_user2", email="init2@test.com", hashed_password=get_password_hash("pass"), role="Employee", department="Operations")
    approver1 = User(username="mgr_user2", email="mgr2@test.com", hashed_password=get_password_hash("pass"), role="Manager", department="Operations")
    db_session.add_all([initiator, approver1])
    db_session.commit()

    tpl = WorkflowTemplate(name="Test Rejection", description="Test", department="Operations", is_active=True)
    db_session.add(tpl)
    db_session.commit()

    stg1 = WorkflowStage(template_id=tpl.id, stage_order=1, name="Initial Stage", required_role="Manager", approval_required=True, sla_hours=12)
    db_session.add(stg1)
    db_session.commit()

    inst = WorkflowEngine.start_workflow(db_session, tpl.id, "Rejection Test", initiator)
    task1 = inst.tasks[0]

    # Reject task at Stage 1
    inst = WorkflowEngine.reject_task(db_session, task1.id, approver1, "Invalid request documents")
    assert inst.status == "REJECTED"
    assert inst.completed_at is not None
