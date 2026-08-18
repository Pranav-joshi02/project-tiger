"""Image management endpoints."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.image import Image, ImageState

router = APIRouter(prefix="/images", tags=["images"])


@router.get("")
def list_images(
    db: Annotated[Session, Depends(get_db)],
    run_id: uuid.UUID | None = None,
    state: ImageState | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """List images with optional filters."""
    query = db.query(Image)
    if run_id:
        query = query.filter(Image.run_id == run_id)
    if state:
        query = query.filter(Image.state == state)
    total = query.count()
    images = query.order_by(Image.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "images": [
            {
                "id": str(img.id),
                "filename": img.filename,
                "state": img.state.value,
                "triage_confidence": img.triage_confidence,
                "triage_category": img.triage_category,
                "size_bytes": img.size_bytes,
                "run_id": str(img.run_id),
                "captured_at": img.captured_at.isoformat() if img.captured_at else None,
                "created_at": img.created_at.isoformat(),
            }
            for img in images
        ],
        "total": total,
    }


@router.get("/{image_id}")
def get_image(image_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    """Get image details."""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return {
        "id": str(image.id),
        "filename": image.filename,
        "sha256": image.sha256,
        "state": image.state.value,
        "triage_confidence": image.triage_confidence,
        "triage_category": image.triage_category,
        "model_version": image.model_version,
        "size_bytes": image.size_bytes,
        "width": image.width,
        "height": image.height,
        "exif_data": image.exif_data,
        "storage_uri": image.storage_uri,
        "run_id": str(image.run_id),
        "captured_at": image.captured_at.isoformat() if image.captured_at else None,
        "created_at": image.created_at.isoformat(),
    }


from pathlib import Path
from fastapi.responses import FileResponse, Response

@router.get("/{image_id}/file")
def get_image_file(image_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    """Stream the actual image binary file."""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    if image.storage_uri:
        p = Path(image.storage_uri)
        if p.exists() and p.is_file():
            content_type = "image/jpeg"
            if p.suffix.lower() == ".png":
                content_type = "image/png"
            elif p.suffix.lower() == ".webp":
                content_type = "image/webp"
            return FileResponse(path=str(p), media_type=content_type)
    
    # Fallback synthetic tiger SVG response if on-disk file is missing
    svg_fallback = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400">
      <rect width="600" height="400" fill="#0f291e"/>
      <rect x="20" y="20" width="560" height="360" rx="12" fill="#143829" stroke="#d4af37" stroke-width="2"/>
      <text x="300" y="160" font-family="sans-serif" font-size="64" text-anchor="middle" fill="#d4af37">🐅</text>
      <text x="300" y="230" font-family="serif" font-weight="bold" font-size="20" text-anchor="middle" fill="#ffffff">{image.filename}</text>
      <text x="300" y="265" font-family="monospace" font-size="13" text-anchor="middle" fill="#10b981">{image.triage_category or 'TIGER'} · ID: {str(image.id)[:8]}</text>
    </svg>"""
    return Response(content=svg_fallback, media_type="image/svg+xml")


@router.patch("/{image_id}/state")
def update_image_state(
    image_id: uuid.UUID,
    new_state: ImageState,
    db: Annotated[Session, Depends(get_db)],
):
    """Update an image's triage state."""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image.state = new_state
    db.commit()
    return {"id": str(image.id), "state": image.state.value}
