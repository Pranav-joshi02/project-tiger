"""Tiger detection task."""
import logging
import uuid
from pathlib import Path

from workers.celery_app import celery_app, get_worker_db

logger = logging.getLogger(__name__)


def _load_detection_model():
    """Load the best available detection model: fine-tuned Pench model or generic COCO."""
    from ml.common.model_loader import load_model

    # Try fine-tuned Pench species detector first
    pench_paths = [
        Path("models/checkpoints/pench-species-detector.pt"),
        Path("/srv/models/checkpoints/pench-species-detector.pt"),
    ]
    for p in pench_paths:
        if p.exists():
            logger.info(f"Loading fine-tuned Pench species detector from {p}")
            return load_model(str(p), task="detect"), True

    # Fallback to generic COCO YOLOv8n
    logger.info("Pench model not found, using generic YOLOv8n")
    return load_model("yolov8n", task="detect"), False


# Non-tiger species to filter out from tiger detections
# Expanded with spotted deer and sloth bear specific classes
NON_TIGER_COCO_CLASSES = {
    "person", "car", "truck", "bus", "motorcycle", "bicycle",
    "elephant", "zebra", "giraffe", "bear", "horse", "sheep", "cow", "dog", "bird",
}

# Pench fine-tuned model class names for non-tiger species
NON_TIGER_PENCH_CLASSES = {
    "spotted_deer", "sloth_bear", "leopard", "other_animal",
}


@celery_app.task(name="workers.tasks.tiger_detection.detect_tigers", queue="detection")
def detect_tigers(run_id: str) -> dict:
    """Run tiger-specific detection on retained images."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))
    from app.models.image import Image, ImageState
    from app.models.detection import Detection, DetectionCategory
    from app.models.run import Run, RunStatus

    db = get_worker_db()
    try:
        images = db.query(Image).filter(
            Image.run_id == uuid.UUID(run_id),
            Image.state == ImageState.ACTIVE,
        ).all()

        tigers_found = 0
        species_counts = {
            "spotted_deer": 0,
            "sloth_bear": 0,
            "other_filtered": 0,
        }

        try:
            model, is_pench_model = _load_detection_model()
        except Exception as e:
            logger.warning(f"Tiger detection model unavailable: {e}")
            return {"run_id": run_id, "tigers_detected": 0, "message": "Model unavailable"}

        for image in images:
            img_path = Path(image.storage_uri) if image.storage_uri else None
            if not img_path or not img_path.exists():
                continue

            results = model(str(img_path), conf=0.40, verbose=False)
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0]) if hasattr(box, "cls") and len(box.cls) > 0 else 0
                    cls_name = model.names[cls_id] if hasattr(model, "names") and isinstance(model.names, dict) and cls_id in model.names else "cat"
                    
                    # Filter non-tiger species using both COCO and Pench class lists
                    if cls_name in NON_TIGER_COCO_CLASSES:
                        if cls_name == "bear":
                            species_counts["sloth_bear"] += 1
                        elif cls_name in ("cow", "horse", "sheep"):
                            # These COCO classes often misrepresent deer
                            species_counts["spotted_deer"] += 1
                        else:
                            species_counts["other_filtered"] += 1
                        continue

                    if is_pench_model and cls_name in NON_TIGER_PENCH_CLASSES:
                        if cls_name == "spotted_deer":
                            species_counts["spotted_deer"] += 1
                        elif cls_name == "sloth_bear":
                            species_counts["sloth_bear"] += 1
                        else:
                            species_counts["other_filtered"] += 1
                        continue

                    detection = Detection(
                        image_id=image.id,
                        category=DetectionCategory.TIGER,
                        confidence=float(box.conf[0]),
                        bbox=box.xyxy[0].tolist(),
                    )
                    db.add(detection)
                    tigers_found += 1

        # Update run stats
        run = db.query(Run).filter(Run.id == uuid.UUID(run_id)).first()
        if run:
            run.tiger_detections = tigers_found
        db.commit()

        logger.info(
            f"Tiger detection: {tigers_found} tigers in run {run_id} "
            f"(filtered: {species_counts['spotted_deer']} deer, "
            f"{species_counts['sloth_bear']} bears, "
            f"{species_counts['other_filtered']} other)"
        )
        
        # Chain to next step
        if tigers_found > 0:
            from workers.tasks.flank_extraction import extract_flanks
            extract_flanks.delay(run_id)
        else:
            from datetime import datetime, timezone
            if run:
                run.status = RunStatus.COMPLETE
                run.completed_at = datetime.now(timezone.utc)
                db.commit()
                
        return {
            "run_id": run_id,
            "tigers_detected": tigers_found,
            "species_filtered": species_counts,
            "using_pench_model": is_pench_model,
        }
    finally:
        db.close()

