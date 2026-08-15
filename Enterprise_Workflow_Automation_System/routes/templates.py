from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.user import User
from models.workflow import WorkflowTemplate, WorkflowStage
from schemas.workflow import WorkflowTemplateCreate, WorkflowTemplateResponse, WorkflowTemplateUpdate
from auth.rbac import get_current_active_user, require_role

router = APIRouter(prefix="/templates", tags=["Workflow Templates"])

@router.post("", response_model=WorkflowTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    template_in: WorkflowTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    template = WorkflowTemplate(
        name=template_in.name,
        description=template_in.description,
        department=template_in.department,
        created_by_id=current_user.id,
        is_active=True
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    for stage_in in template_in.stages:
        stage = WorkflowStage(
            template_id=template.id,
            stage_order=stage_in.stage_order,
            name=stage_in.name,
            required_role=stage_in.required_role,
            required_department=stage_in.required_department,
            assigned_user_id=stage_in.assigned_user_id,
            approval_required=stage_in.approval_required,
            sla_hours=stage_in.sla_hours
        )
        db.add(stage)

    db.commit()
    db.refresh(template)
    return template

@router.get("", response_model=List[WorkflowTemplateResponse])
def get_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return db.query(WorkflowTemplate).filter(WorkflowTemplate.is_active == True).all()

@router.get("/{id}", response_model=WorkflowTemplateResponse)
def get_template_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    template = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow template not found")
    return template

@router.put("/{id}", response_model=WorkflowTemplateResponse)
def update_template(
    id: int,
    template_in: WorkflowTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    template = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow template not found")

    if template_in.name is not None:
        template.name = template_in.name
    if template_in.description is not None:
        template.description = template_in.description
    if template_in.department is not None:
        template.department = template_in.department
    if template_in.is_active is not None:
        template.is_active = template_in.is_active

    if template_in.stages is not None:
        # Replace existing stages dynamically
        db.query(WorkflowStage).filter(WorkflowStage.template_id == template.id).delete()
        for stage_in in template_in.stages:
            stage = WorkflowStage(
                template_id=template.id,
                stage_order=stage_in.stage_order,
                name=stage_in.name,
                required_role=stage_in.required_role,
                required_department=stage_in.required_department,
                assigned_user_id=stage_in.assigned_user_id,
                approval_required=stage_in.approval_required,
                sla_hours=stage_in.sla_hours
            )
            db.add(stage)

    db.commit()
    db.refresh(template)
    return template

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    template = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow template not found")
    
    template.is_active = False
    db.commit()
    return None
