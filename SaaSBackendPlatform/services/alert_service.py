from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from models.alert import Alert
from models.subscription import TenantSubscription
from schemas.alert import AlertCreate

class AlertService:
    @staticmethod
    def create_alert(db: Session, org_id: int, user_id: int, alert_data: AlertCreate) -> Alert:
        # Check active tenant subscription alert limit
        tenant_sub = db.query(TenantSubscription).filter(
            TenantSubscription.organization_id == org_id,
            TenantSubscription.status == "active"
        ).first()

        max_alerts = tenant_sub.plan.max_alerts if tenant_sub and tenant_sub.plan else 10

        # Note: max_alerts < 0 or max_alerts >= 999999 means Unlimited (Premium)
        if max_alerts >= 0 and max_alerts < 999999:
            current_alert_count = db.query(Alert).filter(Alert.organization_id == org_id).count()
            if current_alert_count >= max_alerts:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Alert quota exceeded for current subscription plan ({current_alert_count}/{max_alerts}). Upgrade plan to issue more alerts."
                )

        alert = Alert(
            organization_id=org_id,
            user_id=user_id,
            title=alert_data.title,
            message=alert_data.message,
            severity=alert_data.severity.upper() if alert_data.severity else "INFO"
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def get_organization_alerts(db: Session, org_id: int, skip: int = 0, limit: int = 100) -> List[Alert]:
        return db.query(Alert).filter(
            Alert.organization_id == org_id
        ).order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def delete_alert(db: Session, org_id: int, alert_id: int) -> bool:
        alert = db.query(Alert).filter(
            Alert.id == alert_id,
            Alert.organization_id == org_id
        ).first()

        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )

        db.delete(alert)
        db.commit()
        return True
