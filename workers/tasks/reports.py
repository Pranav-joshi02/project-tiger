"""Report generation task."""
import logging
import uuid
from pathlib import Path

from workers.celery_app import celery_app, get_worker_db

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.reports.generate_report", queue="reports")
def generate_report(run_id: str, report_type: str = "summary") -> dict:
    """Generate a report for a processing run."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))
    from app.models.run import Run

    db = get_worker_db()
    try:
        run = db.query(Run).filter(Run.id == uuid.UUID(run_id)).first()
        if not run:
            return {"error": f"Run {run_id} not found"}

        report = {
            "run_id": run_id,
            "run_name": run.name,
            "report_type": report_type,
            "total_images": run.total_images,
            "quarantined": run.quarantined_images,
            "retained": run.retained_images,
            "tiger_detections": run.tiger_detections,
            "auto_matched": run.auto_matched,
            "new_tigers": run.new_tigers,
            "for_review": run.for_review,
        }

        logger.info(f"Report generated for run {run_id}")
        return report
    finally:
        db.close()
