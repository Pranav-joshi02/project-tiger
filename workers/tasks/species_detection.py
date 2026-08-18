"""Species classification task."""
import logging
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.species_detection.detect_species", queue="detection")
def detect_species(run_id: str) -> dict:
    """Run species classification on detected animals."""
    # Placeholder — MegaDetector triage handles basic classification
    logger.info(f"Species detection placeholder for run {run_id}")
    return {"run_id": run_id, "status": "deferred_to_triage"}
