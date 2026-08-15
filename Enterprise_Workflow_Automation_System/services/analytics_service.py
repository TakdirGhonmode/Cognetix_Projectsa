from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.instance import WorkflowInstance, TaskInstance
from models.workflow import WorkflowTemplate, WorkflowStage
from schemas.analytics import (
    ApprovalTimeMetrics, TemplateApprovalTime, StageApprovalTime,
    BottleneckMetrics, BottleneckItem, CompletionRateMetrics
)

def calculate_approval_times(db: Session) -> ApprovalTimeMetrics:
    templates = db.query(WorkflowTemplate).all()
    template_metrics = []
    all_durations = []

    for template in templates:
        stage_metrics = []
        for stage in template.stages:
            approved_tasks = db.query(TaskInstance).filter(
                TaskInstance.stage_id == stage.id,
                TaskInstance.status == "APPROVED",
                TaskInstance.completed_at.isnot(None)
            ).all()

            durations = []
            for t in approved_tasks:
                if t.completed_at and t.created_at:
                    created = t.created_at.replace(tzinfo=timezone.utc) if t.created_at.tzinfo is None else t.created_at
                    completed = t.completed_at.replace(tzinfo=timezone.utc) if t.completed_at.tzinfo is None else t.completed_at
                    hours = (completed - created).total_seconds() / 3600.0
                    durations.append(hours)
                    all_durations.append(hours)

            avg_stage_hours = round(sum(durations) / len(durations), 2) if durations else 0.0
            stage_metrics.append(StageApprovalTime(stage_name=stage.name, avg_hours=avg_stage_hours))

        stage_avgs = [s.avg_hours for s in stage_metrics if s.avg_hours > 0]
        avg_template_hours = round(sum(stage_avgs) / len(stage_avgs), 2) if stage_avgs else 0.0
        template_metrics.append(TemplateApprovalTime(
            template_id=template.id,
            template_name=template.name,
            avg_hours=avg_template_hours,
            stages=stage_metrics
        ))

    overall_avg = round(sum(all_durations) / len(all_durations), 2) if all_durations else 0.0

    return ApprovalTimeMetrics(
        overall_avg_hours=overall_avg,
        templates=template_metrics
    )


def calculate_bottlenecks(db: Session) -> BottleneckMetrics:
    pending_tasks = db.query(TaskInstance).filter(TaskInstance.status == "PENDING").all()
    now_utc = datetime.now(timezone.utc)

    stage_map = {}
    for task in pending_tasks:
        stage = db.query(WorkflowStage).filter(WorkflowStage.id == task.stage_id).first()
        if not stage:
            continue
        template = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == stage.template_id).first()
        template_name = template.name if template else "Unknown"

        created = task.created_at.replace(tzinfo=timezone.utc) if task.created_at.tzinfo is None else task.created_at
        wait_hours = (now_utc - created).total_seconds() / 3600.0
        is_overdue = wait_hours > stage.sla_hours

        key = (stage.id, stage.name, template_name, stage.sla_hours)
        if key not in stage_map:
            stage_map[key] = {
                "pending_count": 0,
                "overdue_count": 0,
                "total_wait_hours": 0.0
            }
        stage_map[key]["pending_count"] += 1
        if is_overdue:
            stage_map[key]["overdue_count"] += 1
        stage_map[key]["total_wait_hours"] += wait_hours

    bottleneck_items = []
    for (stage_id, stage_name, template_name, sla_hours), data in stage_map.items():
        count = data["pending_count"]
        overdue = data["overdue_count"]
        avg_wait = round(data["total_wait_hours"] / count, 2) if count > 0 else 0.0

        if overdue > 3 or avg_wait > (sla_hours * 2):
            severity = "CRITICAL"
        elif overdue > 0 or avg_wait > sla_hours:
            severity = "HIGH"
        elif count >= 3:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        bottleneck_items.append(BottleneckItem(
            stage_name=stage_name,
            template_name=template_name,
            pending_tasks_count=count,
            overdue_sla_count=overdue,
            avg_wait_hours=avg_wait,
            status_severity=severity
        ))

    # Sort bottlenecks by severity: CRITICAL > HIGH > MEDIUM > LOW
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    bottleneck_items.sort(key=lambda x: severity_order.get(x.status_severity, 4))

    return BottleneckMetrics(
        total_bottlenecks=len(bottleneck_items),
        items=bottleneck_items
    )


def calculate_completion_rates(db: Session) -> CompletionRateMetrics:
    total_instances = db.query(WorkflowInstance).count()
    completed_count = db.query(WorkflowInstance).filter(WorkflowInstance.status == "COMPLETED").count()
    rejected_count = db.query(WorkflowInstance).filter(WorkflowInstance.status == "REJECTED").count()
    in_progress_count = db.query(WorkflowInstance).filter(
        WorkflowInstance.status.in_(["PENDING", "IN_PROGRESS", "MODIFICATION_REQUESTED"])
    ).count()

    completion_rate = round((completed_count / total_instances * 100.0), 2) if total_instances > 0 else 0.0
    rejection_rate = round((rejected_count / total_instances * 100.0), 2) if total_instances > 0 else 0.0

    return CompletionRateMetrics(
        total_instances=total_instances,
        completed_count=completed_count,
        rejected_count=rejected_count,
        in_progress_count=in_progress_count,
        completion_rate_percent=completion_rate,
        rejection_rate_percent=rejection_rate
    )
