"""Deduplication task — flags duplicate images by SHA256 hash."""
import logging
import uuid
from pathlib import Path

from workers.celery_app import celery_app, get_worker_db

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.deduplication.deduplicate_run", queue="ingestion")
def deduplicate_run(run_id: str) -> dict:
    """Check for cross-run duplicates using SHA256 hashes."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))
    from app.models.image import Image, ImageState

    db = get_worker_db()
    try:
        images = db.query(Image).filter(
            Image.run_id == uuid.UUID(run_id),
            Image.state == ImageState.PENDING,
        ).all()

        cross_dupes = 0
        for img in images:
            existing = db.query(Image).filter(
                Image.sha256 == img.sha256,
                Image.run_id != uuid.UUID(run_id),
                Image.state != ImageState.DUPLICATE,
            ).first()
            if existing:
                img.state = ImageState.DUPLICATE
                cross_dupes += 1

        db.commit()
        logger.info(f"Found {cross_dupes} cross-run duplicates for run {run_id}")
        return {"run_id": run_id, "cross_duplicates": cross_dupes}
    finally:
        db.close()
