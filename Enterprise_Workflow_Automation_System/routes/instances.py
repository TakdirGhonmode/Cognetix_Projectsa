from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.user import User
from models.instance import WorkflowInstance
from schemas.instance import WorkflowInstanceCreate, WorkflowInstanceResponse
from auth.rbac import get_current_active_user
from workflow_engine import WorkflowEngine

router = APIRouter(prefix="/instances", tags=["Workflow Execution"])

@router.post("", response_model=WorkflowInstanceResponse, status_code=status.HTTP_201_CREATED)
def start_instance(
    instance_in: WorkflowInstanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return WorkflowEngine.start_workflow(
        db=db,
        template_id=instance_in.template_id,
        title=instance_in.title,
        initiator=current_user,
        payload_data=instance_in.payload
    )

@router.get("", response_model=List[WorkflowInstanceResponse])
def list_instances(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(WorkflowInstance)
    if status_filter:
        query = query.filter(WorkflowInstance.status == status_filter)
    return query.order_by(WorkflowInstance.id.desc()).all()

@router.get("/active", response_model=List[WorkflowInstanceResponse])
def list_active_instances(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return db.query(WorkflowInstance).filter(
        WorkflowInstance.status.in_(["PENDING", "IN_PROGRESS", "MODIFICATION_REQUESTED"])
    ).order_by(WorkflowInstance.id.desc()).all()

@router.get("/completed", response_model=List[WorkflowInstanceResponse])
def list_completed_instances(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return db.query(WorkflowInstance).filter(
        WorkflowInstance.status.in_(["COMPLETED", "REJECTED"])
    ).order_by(WorkflowInstance.id.desc()).all()

@router.get("/{id}", response_model=WorkflowInstanceResponse)
def get_instance_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    instance = db.query(WorkflowInstance).filter(WorkflowInstance.id == id).first()
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow instance not found")
    return instance
