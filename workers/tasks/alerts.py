"""Alert generation task."""
import logging
import uuid
from pathlib import Path

from workers.celery_app import celery_app, get_worker_db

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.alerts.generate_alerts", queue="alerts")
def generate_alerts(run_id: str, tiger_ids: list[str] | None = None) -> dict:
    """Generate alerts based on spatial and behavioral analysis."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))
    from app.models.alert import Alert, AlertType, AlertSeverity, AlertStatus
    from app.models.observation import Observation

    from alerts.engine import run_alert_engine

    db = get_worker_db()
    try:
        if tiger_ids is None:
            from app.models.tiger import Tiger
            tiger_ids = [str(t.id) for t in db.query(Tiger).all()]

        alerts_created = 0
        for tid in tiger_ids:
            observations = [
                {
                    "tiger_id": tid,
                    "station_id": str(o.station_id),
                    "captured_at": o.captured_at.isoformat(),
                    "zone": o.station.zone.value if o.station else "CORE",
                }
                for o in db.query(Observation).filter(Observation.tiger_id == uuid.UUID(tid)).all()
            ]

            alert_results = run_alert_engine(tid, observations)
            for alert_data in alert_results:
                alert = Alert(
                    tiger_id=uuid.UUID(tid),
                    type=AlertType(alert_data.get("type", "BUFFER_MOVEMENT")),
                    severity=AlertSeverity(alert_data.get("severity", "MEDIUM").upper()),
                    status=AlertStatus.ACTIVE,
                    title=alert_data.get("type", "Alert"),
                    summary=alert_data.get("details", ""),
                    evidence=alert_data.get("evidence"),
                )
                db.add(alert)
                alerts_created += 1

        db.commit()
        logger.info(f"Generated {alerts_created} alerts for run {run_id}")
        return {"run_id": run_id, "alerts_created": alerts_created}
    finally:
        db.close()
