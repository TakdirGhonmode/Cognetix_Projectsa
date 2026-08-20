from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.user import User
from models.instance import TaskInstance, WorkflowInstance
from schemas.task import TaskResponse, TaskActionRequest
from schemas.instance import WorkflowInstanceResponse
from auth.rbac import get_current_active_user
from workflow_engine import WorkflowEngine

router = APIRouter(prefix="/tasks", tags=["Task Management"])

@router.get("", response_model=List[TaskResponse])
def list_all_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return db.query(TaskInstance).order_by(TaskInstance.id.desc()).all()

@router.get("/pending", response_model=List[TaskResponse])
def get_pending_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return WorkflowEngine.get_pending_tasks_for_user(db, current_user)

@router.post("/{id}/approve", response_model=WorkflowInstanceResponse)
def approve_task(
    id: int,
    action_in: Optional[TaskActionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    comments = action_in.comments if action_in else "Approved"
    return WorkflowEngine.approve_task(
        db=db,
        task_id=id,
        actor=current_user,
        comments=comments
    )

@router.post("/{id}/reject", response_model=WorkflowInstanceResponse)
def reject_task(
    id: int,
    action_in: TaskActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    reason = action_in.reason or action_in.comments
    if not reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejection reason is required."
        )
    return WorkflowEngine.reject_task(
        db=db,
        task_id=id,
        actor=current_user,
        reason=reason
    )

@router.post("/{id}/modify", response_model=WorkflowInstanceResponse)
def request_modification(
    id: int,
    action_in: TaskActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    comments = action_in.comments or action_in.reason
    if not comments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Modification comments/instructions are required."
        )
    return WorkflowEngine.request_modification(
        db=db,
        task_id=id,
        actor=current_user,
        comments=comments
    )
