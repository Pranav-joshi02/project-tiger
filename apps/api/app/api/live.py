import os
import shutil
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.run import Run, RunStatus
from app.services.live_pipeline_service import LivePipelineService

router = APIRouter(prefix="/live", tags=["live capture"])


@router.post("/capture", status_code=status.HTTP_200_OK)
def live_capture(
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Accepts a live webcam capture or uploaded picture, runs real-time
    species triage (tiger vs non-tiger) and Tiger Re-ID matching on PostgreSQL.
    """
    run_id = uuid.uuid4()
    source_dir_name = f"live_{run_id.hex[:8]}"
    
    storage_root = Path(settings.storage_root)
    if not storage_root.is_absolute():
        cur = Path(__file__).resolve().parent
        found = None
        for p in [cur, *cur.parents, Path.cwd()]:
            if (p / "storage").exists() or (p / "apps").exists():
                found = p / "storage"
                break
        storage_root = found if found else Path.cwd() / "storage"
        
    upload_dir = storage_root / "raw" / source_dir_name
    upload_dir.mkdir(parents=True, exist_ok=True)

    
    filename = file.filename or "live_capture.jpg"
    file_path = upload_dir / filename
    
    # Save the file
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create the run in PostgreSQL DB
    run = Run(
        id=run_id,
        name=f"Live Capture {run_id.hex[:6]}",
        source_directory=source_dir_name,
        status=RunStatus.PENDING,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    
    # Execute the multi-stage pipeline directly in-process for instant response
    try:
        pipeline_result = LivePipelineService.process_live_image(
            image_path=file_path,
            run_id=run.id,
            db=db,
        )
        return pipeline_result
    except Exception as e:
        import traceback
        traceback.print_exc()
        run.status = RunStatus.FAILED
        run.error_message = str(e)
        db.commit()
        return {
            "status": "ERROR",
            "is_tiger": False,
            "stage": "ERROR",
            "message": f"Processing failed: {str(e)}",
            "run_id": str(run.id),
        }
