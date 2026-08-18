"""Processing run management."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.image import Image, ImageState
from app.models.run import Run, RunStatus

router = APIRouter(prefix="/runs", tags=["processing runs"])


class RunCreate(BaseModel):
    name: str = Field(description="Human-readable run name")
    source_directory: str = Field(description="Directory below configured raw storage root")


class RunResponse(BaseModel):
    id: str
    name: str
    status: str
    source_directory: str
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    total_images: int = 0
    duplicate_images: int = 0
    quarantined_images: int = 0
    retained_images: int = 0
    tiger_detections: int = 0
    new_tigers: int = 0
    auto_matched: int = 0
    for_review: int = 0
    quarantined_bytes: int = 0
    processing_duration_seconds: float | None = None


def _run_to_response(run: Run) -> dict:
    return {
        "id": str(run.id),
        "name": run.name,
        "status": run.status.value,
        "source_directory": run.source_directory,
        "created_at": run.created_at.isoformat(),
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "total_images": run.total_images,
        "duplicate_images": run.duplicate_images,
        "quarantined_images": run.quarantined_images,
        "retained_images": run.retained_images,
        "tiger_detections": run.tiger_detections,
        "new_tigers": run.new_tigers,
        "auto_matched": run.auto_matched,
        "for_review": run.for_review,
        "quarantined_bytes": run.quarantined_bytes,
        "processing_duration_seconds": run.processing_duration_seconds,
    }


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def create_run(payload: RunCreate, db: Annotated[Session, Depends(get_db)]):
    """Create a new processing run and dispatch to Celery worker."""
    run = Run(
        name=payload.name,
        source_directory=payload.source_directory,
        status=RunStatus.PENDING,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Dispatch Celery task (import here to avoid circular imports)
    try:
        from workers.celery_app import celery_app
        celery_app.send_task(
            "workers.tasks.ingestion.ingest_run",
            args=[str(run.id), payload.source_directory],
            queue="ingestion",
        )
    except Exception:
        # If Celery is not available, mark as pending for manual processing
        pass

    return _run_to_response(run)


@router.get("")
def list_runs(db: Annotated[Session, Depends(get_db)], limit: int = 50, offset: int = 0):
    """List all processing runs."""
    runs = db.query(Run).order_by(Run.created_at.desc()).offset(offset).limit(limit).all()
    total = db.query(Run).count()
    return {"runs": [_run_to_response(r) for r in runs], "total": total}


@router.get("/{run_id}")
def get_run(run_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    """Get a specific processing run with details."""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return _run_to_response(run)


@router.post("/{run_id}/restore")
def restore_quarantine(run_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    """Restore quarantined images from a run."""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    restored = (
        db.query(Image)
        .filter(Image.run_id == run_id, Image.state == ImageState.QUARANTINED)
        .update({Image.state: ImageState.RESTORED})
    )
    db.commit()
    return {"run_id": str(run_id), "restored": restored, "audit_event": "BATCH_RESTORE"}
