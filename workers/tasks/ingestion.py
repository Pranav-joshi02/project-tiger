"""Image ingestion task — scans directory, hashes files, stores metadata."""
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

from workers.celery_app import celery_app, get_worker_db

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def _sha256(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@celery_app.task(name="workers.tasks.ingestion.ingest_run", bind=True, queue="ingestion")
def ingest_run(self, run_id: str, source_directory: str) -> dict:
    """Ingest images from a directory into the database."""
    import os
    import uuid
    # Import models inline to avoid import-time DB connection
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))
    from app.models.image import Image, ImageState
    from app.models.run import Run, RunStatus

    db = get_worker_db()
    try:
        run = db.query(Run).filter(Run.id == uuid.UUID(run_id)).first()
        if not run:
            return {"error": f"Run {run_id} not found"}

        run.status = RunStatus.INGESTING
        run.started_at = datetime.now(timezone.utc)
        db.commit()

        storage_root = Path(os.getenv("STORAGE_ROOT", "storage"))
        source = storage_root / "raw" / source_directory

        if not source.is_dir():
            run.status = RunStatus.FAILED
            run.error_message = f"Source directory not found: {source}"
            db.commit()
            return {"error": run.error_message}

        # Scan for images
        image_paths = [
            p for p in source.rglob("*")
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        ]

        seen_hashes: set[str] = set()
        total = 0
        duplicates = 0

        for img_path in image_paths:
            sha = _sha256(img_path)
            total += 1

            if sha in seen_hashes:
                duplicates += 1
                state = ImageState.DUPLICATE
            else:
                seen_hashes.add(sha)
                state = ImageState.PENDING

            image = Image(
                run_id=uuid.UUID(run_id),
                filename=img_path.name,
                sha256=sha,
                size_bytes=img_path.stat().st_size,
                storage_uri=str(img_path),
                state=state,
            )
            db.add(image)

        run.total_images = total
        run.duplicate_images = duplicates
        db.commit()

        logger.info(f"Ingested {total} images ({duplicates} duplicates) for run {run_id}")

        # Chain to triage
        from workers.tasks.triage import triage_run
        triage_run.delay(run_id)

        return {
            "run_id": run_id,
            "total_images": total,
            "duplicates": duplicates,
            "status": "ingested",
        }
    except Exception as e:
        logger.error(f"Ingestion failed for run {run_id}: {e}")
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
