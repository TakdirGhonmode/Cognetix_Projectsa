from models.user import User
from models.workflow import WorkflowTemplate, WorkflowStage
from workflow_engine import WorkflowEngine
from services.audit_service import verify_audit_trail_integrity
from auth.security import get_password_hash

def test_audit_log_hash_chaining(db_session):
    u = User(username="audit_user", email="audit@test.com", hashed_password=get_password_hash("pass"), role="Admin", department="Executive")
    db_session.add(u)
    db_session.commit()

    tpl = WorkflowTemplate(name="Audit Tpl", description="Desc", department="Executive", is_active=True)
    db_session.add(tpl)
    db_session.commit()

    stg = WorkflowStage(template_id=tpl.id, stage_order=1, name="Stage 1", required_role="Admin")
    db_session.add(stg)
    db_session.commit()

    inst = WorkflowEngine.start_workflow(db_session, tpl.id, "Audit Test", u)
    task = inst.tasks[0]
    WorkflowEngine.approve_task(db_session, task.id, u, "Audit approved")

    verify_res = verify_audit_trail_integrity(db_session)
    assert verify_res.is_valid is True
    assert verify_res.total_records >= 2
    assert len(verify_res.corrupted_records) == 0
