"""Conservation alert management."""
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.alert import Alert, AlertSeverity, AlertStatus, AlertType

router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertStatusUpdate(BaseModel):
    status: AlertStatus


@router.get("")
def list_alerts(
    db: Annotated[Session, Depends(get_db)],
    status: AlertStatus | None = None,
    severity: AlertSeverity | None = None,
    alert_type: AlertType | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    """List alerts with optional filters."""
    query = db.query(Alert)
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    if alert_type:
        query = query.filter(Alert.type == alert_type)
    total = query.count()
    alerts = query.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "alerts": [
            {
                "id": str(a.id),
                "type": a.type.value,
                "severity": a.severity.value,
                "status": a.status.value,
                "title": a.title,
                "summary": a.summary,
                "evidence": a.evidence,
                "tiger_id": str(a.tiger_id) if a.tiger_id else None,
                "rule_version": a.rule_version,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ],
        "total": total,
    }


@router.get("/{alert_id}")
def get_alert(alert_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {
        "id": str(alert.id),
        "type": alert.type.value,
        "severity": alert.severity.value,
        "status": alert.status.value,
        "title": alert.title,
        "summary": alert.summary,
        "evidence": alert.evidence,
        "tiger_id": str(alert.tiger_id) if alert.tiger_id else None,
        "rule_version": alert.rule_version,
        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
        "created_at": alert.created_at.isoformat(),
    }


@router.patch("/{alert_id}")
def update_alert(
    alert_id: uuid.UUID,
    payload: AlertStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    """Update alert status."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = payload.status
    if payload.status == AlertStatus.ACKNOWLEDGED:
        alert.acknowledged_at = datetime.now(timezone.utc)
    elif payload.status in (AlertStatus.RESOLVED, AlertStatus.DISMISSED):
        alert.resolved_at = datetime.now(timezone.utc)

    db.commit()
    return {
        "id": str(alert.id),
        "status": alert.status.value,
        "audit_event": "ALERT_STATUS_CHANGED",
    }


@router.get("/stats/summary")
def alert_stats(db: Annotated[Session, Depends(get_db)]):
    """Alert statistics."""
    active = db.query(func.count(Alert.id)).filter(Alert.status == AlertStatus.ACTIVE).scalar() or 0
    acknowledged = db.query(func.count(Alert.id)).filter(Alert.status == AlertStatus.ACKNOWLEDGED).scalar() or 0
    investigating = db.query(func.count(Alert.id)).filter(Alert.status == AlertStatus.INVESTIGATING).scalar() or 0
    resolved = db.query(func.count(Alert.id)).filter(Alert.status == AlertStatus.RESOLVED).scalar() or 0
    return {"active": active, "acknowledged": acknowledged, "investigating": investigating, "resolved": resolved}
