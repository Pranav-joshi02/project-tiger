"""Dashboard API — aggregated metrics for the overview page."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.alert import Alert, AlertStatus
from app.models.image import Image, ImageState
from app.models.review import Review, ReviewState
from app.models.run import Run, RunStatus
from app.models.tiger import Tiger

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard(db: Annotated[Session, Depends(get_db)]):
    """Return aggregated metrics for the dashboard overview."""
    # Image counts
    total_images = db.query(func.count(Image.id)).scalar() or 0
    quarantined = db.query(func.count(Image.id)).filter(Image.state == ImageState.QUARANTINED).scalar() or 0
    quarantined_bytes = db.query(func.coalesce(func.sum(Image.size_bytes), 0)).filter(Image.state == ImageState.QUARANTINED).scalar()

    # Tiger count
    known_individuals = db.query(func.count(Tiger.id)).scalar() or 0

    # Review queue
    review_queue = db.query(func.count(Review.id)).filter(
        Review.state.in_([ReviewState.PENDING, ReviewState.OPEN])
    ).scalar() or 0

    # Active alerts
    active_alerts = db.query(Alert).filter(
        Alert.status.in_([AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED, AlertStatus.INVESTIGATING])
    ).order_by(Alert.created_at.desc()).limit(10).all()

    # Latest run
    latest_run = db.query(Run).order_by(Run.created_at.desc()).first()

    return {
        "data_notice": "DEMONSTRATION DATA — NOT OPERATIONAL WILDLIFE LOCATION DATA",
        "metrics": {
            "images_processed": total_images,
            "quarantined": quarantined,
            "storage_saved_bytes": quarantined_bytes,
            "known_individuals": known_individuals,
            "review_queue": review_queue,
        },
        "latest_run": {
            "id": str(latest_run.id) if latest_run else None,
            "name": latest_run.name if latest_run else None,
            "status": latest_run.status.value if latest_run else None,
            "total_images": latest_run.total_images if latest_run else 0,
            "retained_images": latest_run.retained_images if latest_run else 0,
            "quarantined_images": latest_run.quarantined_images if latest_run else 0,
            "tiger_detections": latest_run.tiger_detections if latest_run else 0,
            "created_at": latest_run.created_at.isoformat() if latest_run else None,
            "completed_at": latest_run.completed_at.isoformat() if latest_run and latest_run.completed_at else None,
            "duration_seconds": latest_run.processing_duration_seconds if latest_run else None,
        },
        "alerts": [
            {
                "id": str(a.id),
                "type": a.type.value,
                "severity": a.severity.value,
                "status": a.status.value,
                "title": a.title,
                "summary": a.summary,
                "created_at": a.created_at.isoformat(),
            }
            for a in active_alerts
        ],
    }
