"""Flank extraction task with pose estimation and body-part alignment.

Upgraded to integrate:
- Side classification via ml.flank.side_classifier (was previously unused)
- Pose estimation for body-part-aware feature extraction
- Quality assessment fed into the Re-ID model
"""
import logging
import uuid
from pathlib import Path

from workers.celery_app import celery_app, get_worker_db

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.flank_extraction.extract_flanks", queue="detection")
def extract_flanks(run_id: str) -> dict:
    """Extract flank regions from tiger detections with pose and quality assessment."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))
    from app.models.detection import Detection, DetectionCategory
    from app.models.flank import Flank, FlankSide
    from app.models.image import Image

    db = get_worker_db()
    try:
        detections = (
            db.query(Detection)
            .join(Image)
            .filter(Image.run_id == uuid.UUID(run_id), Detection.category == DetectionCategory.TIGER)
            .all()
        )

        flanks_created = 0
        pose_estimated = 0

        for det in detections:
            image = det.image if hasattr(det, "image") else None

            # --- Side classification (previously unused, now integrated) ---
            side = FlankSide.UNKNOWN
            blur_score = None
            exposure_score = None
            quality_score = 0.0

            if image and image.storage_uri:
                try:
                    from ml.flank.side_classifier import classify_flank
                    assessment = classify_flank(image.storage_uri)
                    side_map = {
                        "LEFT": FlankSide.LEFT,
                        "RIGHT": FlankSide.RIGHT,
                    }
                    side = side_map.get(assessment.side, FlankSide.UNKNOWN)
                    blur_score = assessment.blur_score
                    exposure_score = assessment.exposure_score
                    quality_score = assessment.quality_score
                except Exception as e:
                    logger.warning(f"Side classification failed for detection {det.id}: {e}")

            # --- Pose estimation (Item #4) ---
            pose_confidence = None
            if image and image.storage_uri:
                try:
                    import cv2
                    import numpy as np
                    from ml.reid.pose_estimator import get_pose_estimator

                    img = cv2.imread(str(image.storage_uri))
                    if img is not None and det.bbox:
                        bbox = tuple(int(v) for v in det.bbox[:4])
                        estimator = get_pose_estimator()
                        pose_result = estimator.estimate(img, bbox)
                        pose_confidence = pose_result.pose_confidence
                        pose_estimated += 1
                except Exception as e:
                    logger.debug(f"Pose estimation skipped for detection {det.id}: {e}")

            # Create flank record with enriched metadata
            flank = Flank(
                detection_id=det.id,
                side=side,
                quality_score=quality_score,
                blur_score=blur_score,
                exposure_score=exposure_score,
            )
            db.add(flank)
            flanks_created += 1

        db.commit()
        logger.info(
            f"Extracted {flanks_created} flanks for run {run_id} "
            f"(pose estimated: {pose_estimated})"
        )

        # Chain to next step
        if flanks_created > 0:
            from workers.tasks.embedding import generate_embeddings
            generate_embeddings.delay(run_id)
        else:
            from app.models.run import Run, RunStatus
            from datetime import datetime, timezone
            run = db.query(Run).filter(Run.id == uuid.UUID(run_id)).first()
            if run:
                run.status = RunStatus.COMPLETE
                run.completed_at = datetime.now(timezone.utc)
                db.commit()

        return {
            "run_id": run_id,
            "flanks_created": flanks_created,
            "pose_estimated": pose_estimated,
        }
    finally:
        db.close()

