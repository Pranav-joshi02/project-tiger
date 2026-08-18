"""Triage task — classify images as blank/animal/person/vehicle using MegaDetector."""
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from shutil import copy2

from workers.celery_app import celery_app, get_worker_db

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.triage.triage_run", bind=True, queue="triage")
def triage_run(self, run_id: str) -> dict:
    """Run MegaDetector triage on all pending images in a run."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))
    from app.models.image import Image, ImageState
    from app.models.run import Run, RunStatus

    db = get_worker_db()
    try:
        run = db.query(Run).filter(Run.id == uuid.UUID(run_id)).first()
        if not run:
            return {"error": f"Run {run_id} not found"}

        run.status = RunStatus.TRIAGING
        db.commit()

        # Lazy-load MegaDetector
        try:
            from app.services.megadetector import MegaDetectorAdapter
            detector = MegaDetectorAdapter(os.getenv("MEGADETECTOR_VERSION", "MDV6-mit-yolov9-c"))
        except Exception as e:
            logger.warning(f"MegaDetector unavailable: {e}. Marking all images for review.")
            detector = None

        images = db.query(Image).filter(
            Image.run_id == uuid.UUID(run_id),
            Image.state == ImageState.PENDING,
        ).all()

        storage_root = Path(os.getenv("STORAGE_ROOT", "storage"))
        quarantine_dir = storage_root / "quarantine" / run_id
        blank_threshold = float(os.getenv("TRIAGE_BLANK_THRESHOLD", "0.30"))
        subject_threshold = float(os.getenv("TRIAGE_SUBJECT_THRESHOLD", "0.80"))

        quarantined = 0
        retained = 0
        review_required = 0
        quarantined_bytes = 0

        for image in images:
            img_path = Path(image.storage_uri) if image.storage_uri else None

            if not img_path or not img_path.exists():
                image.state = ImageState.REVIEW_REQUIRED
                image.model_version = "file-missing"
                review_required += 1
                continue

            if detector:
                result = detector.evaluate(img_path, blank_threshold, subject_threshold)
                image.triage_confidence = result.max_subject_confidence
                image.model_version = result.model_version

                if result.status == "QUARANTINED":
                    image.state = ImageState.QUARANTINED
                    image.triage_category = "blank"
                    # Copy to quarantine
                    quarantine_dir.mkdir(parents=True, exist_ok=True)
                    dest = quarantine_dir / image.filename
                    try:
                        copy2(img_path, dest)
                        image.quarantine_uri = str(dest)
                    except Exception as e:
                        logger.warning(f"Failed to copy to quarantine: {e}")
                    quarantined += 1
                    quarantined_bytes += image.size_bytes
                elif result.status == "ACTIVE":
                    image.state = ImageState.ACTIVE
                    image.triage_category = "animal"
                    retained += 1
                else:
                    image.state = ImageState.REVIEW_REQUIRED
                    review_required += 1
            else:
                image.state = ImageState.REVIEW_REQUIRED
                image.model_version = "unavailable"
                review_required += 1

        run.quarantined_images = quarantined
        run.retained_images = retained
        run.for_review = review_required
        run.quarantined_bytes = quarantined_bytes
        if run.started_at:
            run.processing_duration_seconds = (
                datetime.now(timezone.utc) - run.started_at
            ).total_seconds()

        db.commit()

        logger.info(
            f"Triage complete for run {run_id}: "
            f"{retained} retained, {quarantined} quarantined, {review_required} for review"
        )
        
        # Chain to next step if there are retained images
        if retained > 0:
            from workers.tasks.tiger_detection import detect_tigers
            detect_tigers.delay(run_id)
        else:
            run = db.query(Run).filter(Run.id == uuid.UUID(run_id)).first()
            if run:
                run.status = RunStatus.COMPLETE
                run.completed_at = datetime.now(timezone.utc)
                db.commit()

        return {
            "run_id": run_id,
            "retained": retained,
            "quarantined": quarantined,
            "review_required": review_required,
            "quarantined_bytes": quarantined_bytes,
        }
    except Exception as e:
        logger.error(f"Triage failed for run {run_id}: {e}")
        try:
            run = db.query(Run).filter(Run.id == uuid.UUID(run_id)).first()
            if run:
                run.status = RunStatus.FAILED
                run.error_message = str(e)
                db.commit()
        except Exception:
            pass
        raise
    finally:
        db.close()
