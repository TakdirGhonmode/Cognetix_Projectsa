import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.user import User
from models.workflow import WorkflowTemplate, WorkflowStage
from models.instance import WorkflowInstance, TaskInstance
from services.audit_service import log_audit_event
from services.notification_service import dispatch_notification

class WorkflowEngine:
    @staticmethod
    def start_workflow(
        db: Session,
        template_id: int,
        title: str,
        initiator: User,
        payload_data: Optional[Dict[str, Any]] = None
    ) -> WorkflowInstance:
        template = db.query(WorkflowTemplate).filter(
            WorkflowTemplate.id == template_id,
            WorkflowTemplate.is_active == True
        ).first()

        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active workflow template not found")

        stages = db.query(WorkflowStage).filter(
            WorkflowStage.template_id == template.id
        ).order_by(WorkflowStage.stage_order.asc()).all()

        if not stages:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workflow template has no configured stages")

        first_stage = stages[0]
        payload_str = json.dumps(payload_data) if payload_data else "{}"

        instance = WorkflowInstance(
            template_id=template.id,
            title=title,
            initiator_id=initiator.id,
            current_stage_id=first_stage.id,
            status="PENDING",
            payload=payload_str
        )
        db.add(instance)
        db.commit()
        db.refresh(instance)

        # Create initial TaskInstance for Stage 1
        task = TaskInstance(
            instance_id=instance.id,
            stage_id=first_stage.id,
            assigned_role=first_stage.required_role,
            assigned_department=first_stage.required_department,
            assigned_user_id=first_stage.assigned_user_id,
            status="PENDING"
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        log_audit_event(
            db=db,
            instance_id=instance.id,
            stage_id=first_stage.id,
            actor_id=initiator.id,
            action="START_WORKFLOW",
            details={
                "title": title,
                "template_name": template.name,
                "initial_stage": first_stage.name,
                "payload": payload_data
            }
        )

        dispatch_notification(
            event_name="WORKFLOW_STARTED",
            payload={"instance_id": instance.id, "title": title, "initiator": initiator.username}
        )

        return instance

    @staticmethod
    def approve_task(
        db: Session,
        task_id: int,
        actor: User,
        comments: Optional[str] = None
    ) -> WorkflowInstance:
        task = db.query(TaskInstance).filter(TaskInstance.id == task_id).first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        if task.status != "PENDING":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Task is already in '{task.status}' status")

        # Validate authorization
        if not WorkflowEngine._can_user_act_on_task(actor, task):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to perform action on this task"
            )

        now_utc = datetime.now(timezone.utc)
        task.status = "APPROVED"
        task.decision_reason = comments or "Approved"
        task.completed_at = now_utc

        instance = db.query(WorkflowInstance).filter(WorkflowInstance.id == task.instance_id).first()
        current_stage = db.query(WorkflowStage).filter(WorkflowStage.id == task.stage_id).first()

        log_audit_event(
            db=db,
            instance_id=instance.id,
            stage_id=current_stage.id,
            actor_id=actor.id,
            action="APPROVED",
            details={"comments": comments, "stage_name": current_stage.name}
        )

        # Check if there is a next stage in template
        next_stage = db.query(WorkflowStage).filter(
            WorkflowStage.template_id == instance.template_id,
            WorkflowStage.stage_order > current_stage.stage_order
        ).order_by(WorkflowStage.stage_order.asc()).first()

        if next_stage:
            # Advance to next stage
            instance.current_stage_id = next_stage.id
            instance.status = "PENDING"

            new_task = TaskInstance(
                instance_id=instance.id,
                stage_id=next_stage.id,
                assigned_role=next_stage.required_role,
                assigned_department=next_stage.required_department,
                assigned_user_id=next_stage.assigned_user_id,
                status="PENDING"
            )
            db.add(new_task)
            db.commit()

            log_audit_event(
                db=db,
                instance_id=instance.id,
                stage_id=next_stage.id,
                actor_id=actor.id,
                action="ROUTE_STAGE",
                details={"from_stage": current_stage.name, "to_stage": next_stage.name}
            )

            dispatch_notification(
                event_name="STAGE_ROUTED",
                payload={"instance_id": instance.id, "to_stage": next_stage.name}
            )
        else:
            # Final stage completed -> Complete workflow
            instance.status = "COMPLETED"
            instance.current_stage_id = None
            instance.completed_at = now_utc
            db.commit()

            log_audit_event(
                db=db,
                instance_id=instance.id,
                stage_id=current_stage.id,
                actor_id=actor.id,
                action="COMPLETED",
                details={"final_stage": current_stage.name}
            )

            dispatch_notification(
                event_name="WORKFLOW_COMPLETED",
                payload={"instance_id": instance.id, "title": instance.title}
            )

        db.refresh(instance)
        return instance

    @staticmethod
    def reject_task(
        db: Session,
        task_id: int,
        actor: User,
        reason: str
    ) -> WorkflowInstance:
        if not reason or not reason.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A detailed rejection reason is mandatory."
            )

        task = db.query(TaskInstance).filter(TaskInstance.id == task_id).first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        if task.status != "PENDING":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Task is already in '{task.status}' status")

        if not WorkflowEngine._can_user_act_on_task(actor, task):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized task action")

        now_utc = datetime.now(timezone.utc)
        task.status = "REJECTED"
        task.decision_reason = reason
        task.completed_at = now_utc

        instance = db.query(WorkflowInstance).filter(WorkflowInstance.id == task.instance_id).first()
        current_stage = db.query(WorkflowStage).filter(WorkflowStage.id == task.stage_id).first()

        log_audit_event(
            db=db,
            instance_id=instance.id,
            stage_id=current_stage.id,
            actor_id=actor.id,
            action="REJECTED",
            details={"reason": reason, "stage_name": current_stage.name}
        )

        # Check if there is a previous stage to route back to
        prev_stage = db.query(WorkflowStage).filter(
            WorkflowStage.template_id == instance.template_id,
            WorkflowStage.stage_order < current_stage.stage_order
        ).order_by(WorkflowStage.stage_order.desc()).first()

        if prev_stage:
            # Route back to previous stage
            instance.current_stage_id = prev_stage.id
            instance.status = "REJECTED"

            new_task = TaskInstance(
                instance_id=instance.id,
                stage_id=prev_stage.id,
                assigned_role=prev_stage.required_role,
                assigned_department=prev_stage.required_department,
                assigned_user_id=prev_stage.assigned_user_id,
                status="PENDING"
            )
            db.add(new_task)
            db.commit()

            log_audit_event(
                db=db,
                instance_id=instance.id,
                stage_id=prev_stage.id,
                actor_id=actor.id,
                action="PREVIOUS_STAGE",
                details={"routed_back_from": current_stage.name, "routed_to": prev_stage.name, "reason": reason}
            )
        else:
            # Stage 1 rejection -> Mark instance REJECTED & terminate workflow
            instance.status = "REJECTED"
            instance.completed_at = now_utc
            db.commit()

        db.refresh(instance)
        return instance

    @staticmethod
    def request_modification(
        db: Session,
        task_id: int,
        actor: User,
        comments: str
    ) -> WorkflowInstance:
        if not comments or not comments.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Modification instructions/comments are required."
            )

        task = db.query(TaskInstance).filter(TaskInstance.id == task_id).first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        if task.status != "PENDING":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Task is already in '{task.status}' status")

        if not WorkflowEngine._can_user_act_on_task(actor, task):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized task action")

        now_utc = datetime.now(timezone.utc)
        task.status = "MODIFICATION_REQUESTED"
        task.decision_reason = comments
        task.completed_at = now_utc

        instance = db.query(WorkflowInstance).filter(WorkflowInstance.id == task.instance_id).first()
        current_stage = db.query(WorkflowStage).filter(WorkflowStage.id == task.stage_id).first()

        instance.status = "MODIFICATION_REQUESTED"

        # Create task assigned back to the workflow initiator for modification
        modification_task = TaskInstance(
            instance_id=instance.id,
            stage_id=current_stage.id,
            assigned_user_id=instance.initiator_id,
            status="PENDING"
        )
        db.add(modification_task)
        db.commit()

        log_audit_event(
            db=db,
            instance_id=instance.id,
            stage_id=current_stage.id,
            actor_id=actor.id,
            action="MODIFICATION_REQUESTED",
            details={"comments": comments, "returned_to_user_id": instance.initiator_id}
        )

        db.refresh(instance)
        return instance

    @staticmethod
    def get_pending_tasks_for_user(db: Session, user: User) -> List[TaskInstance]:
        query = db.query(TaskInstance).filter(TaskInstance.status == "PENDING")

        if user.role == "Admin":
            return query.all()

        filters = []
        if user.id:
            filters.append(TaskInstance.assigned_user_id == user.id)
        if user.role:
            filters.append(TaskInstance.assigned_role == user.role)
        if user.department:
            filters.append(TaskInstance.assigned_department == user.department)

        from sqlalchemy import or_
        return query.filter(or_(*filters)).all()

    @staticmethod
    def _can_user_act_on_task(user: User, task: TaskInstance) -> bool:
        if user.role == "Admin":
            return True
        if task.assigned_user_id is not None and task.assigned_user_id == user.id:
            return True
        if task.assigned_role is not None and task.assigned_role == user.role:
            return True
        if task.assigned_department is not None and task.assigned_department == user.department:
            return True
        return False
