"""Tiger individual management."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.observation import Observation
from app.models.tiger import Tiger, TigerSex, TigerStatus

router = APIRouter(prefix="/tigers", tags=["tigers"])


class TigerCreate(BaseModel):
    code: str
    name: str | None = None
    sex: TigerSex = TigerSex.UNKNOWN
    notes: str | None = None


class TigerUpdate(BaseModel):
    name: str | None = None
    sex: TigerSex | None = None
    status: TigerStatus | None = None
    notes: str | None = None


def _tiger_to_dict(tiger: Tiger) -> dict:
    return {
        "id": str(tiger.id),
        "code": tiger.code,
        "name": tiger.name,
        "sex": tiger.sex.value,
        "status": tiger.status.value,
        "total_observations": tiger.total_observations,
        "first_seen": tiger.first_seen.isoformat() if tiger.first_seen else None,
        "last_seen": tiger.last_seen.isoformat() if tiger.last_seen else None,
        "notes": tiger.notes,
        "created_at": tiger.created_at.isoformat(),
    }


@router.get("")
def list_tigers(
    db: Annotated[Session, Depends(get_db)],
    status: TigerStatus | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """List all known tiger individuals."""
    query = db.query(Tiger).filter(Tiger.status != TigerStatus.MERGED)
    if status:
        query = query.filter(Tiger.status == status)
    if search:
        query = query.filter(
            (Tiger.code.ilike(f"%{search}%")) | (Tiger.name.ilike(f"%{search}%"))
        )
    total = query.count()
    tigers = query.order_by(Tiger.last_seen.desc().nullslast()).offset(offset).limit(limit).all()
    return {"tigers": [_tiger_to_dict(t) for t in tigers], "total": total}


@router.post("", status_code=201)
def create_tiger(payload: TigerCreate, db: Annotated[Session, Depends(get_db)]):
    """Manually enroll a new tiger individual."""
    existing = db.query(Tiger).filter(Tiger.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Tiger code '{payload.code}' already exists")
    tiger = Tiger(code=payload.code, name=payload.name, sex=payload.sex, notes=payload.notes)
    db.add(tiger)
    db.commit()
    db.refresh(tiger)
    return _tiger_to_dict(tiger)


@router.get("/{tiger_id}")
def get_tiger(tiger_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    """Get tiger details with observation history."""
    tiger = db.query(Tiger).filter(Tiger.id == tiger_id).first()
    if not tiger:
        raise HTTPException(status_code=404, detail="Tiger not found")

    observations = (
        db.query(Observation)
        .filter(Observation.tiger_id == tiger_id)
        .order_by(Observation.captured_at.desc())
        .limit(100)
        .all()
    )

    result = _tiger_to_dict(tiger)
    result["observations"] = [
        {
            "id": str(obs.id),
            "station_id": str(obs.station_id),
            "identity_confidence": obs.identity_confidence,
            "identity_method": obs.identity_method,
            "flank_side": obs.flank_side,
            "captured_at": obs.captured_at.isoformat(),
        }
        for obs in observations
    ]
    result["identity_note"] = "Evidence confidence is not biological certainty."
    return result


from pathlib import Path
from fastapi.responses import FileResponse, Response
from app.models.image import Image

@router.get("/{tiger_id}/photo")
def get_tiger_photo(tiger_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    """Retrieve reference photo / crop for a tiger individual."""
    tiger = db.query(Tiger).filter(Tiger.id == tiger_id).first()
    if not tiger:
        raise HTTPException(status_code=404, detail="Tiger not found")

    # Look for most recent observation with image
    obs = db.query(Observation).filter(Observation.tiger_id == tiger.id).order_by(Observation.captured_at.desc()).first()
    if obs and obs.image_id:
        img = db.query(Image).filter(Image.id == obs.image_id).first()
        if img and img.storage_uri:
            p = Path(img.storage_uri)
            if p.exists() and p.is_file():
                content_type = "image/jpeg"
                if p.suffix.lower() == ".png":
                    content_type = "image/png"
                return FileResponse(path=str(p), media_type=content_type)

    # Return high-quality SVG badge representation if raw file is not present
    svg_badge = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400">
      <defs>
        <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#064e3b"/>
          <stop offset="100%" stop-color="#022c22"/>
        </linearGradient>
      </defs>
      <rect width="600" height="400" fill="url(#g)"/>
      <circle cx="300" cy="160" r="70" fill="#047857" stroke="#d4af37" stroke-width="3"/>
      <text x="300" y="185" font-family="sans-serif" font-size="64" text-anchor="middle" fill="#d4af37">🐅</text>
      <text x="300" y="275" font-family="serif" font-weight="bold" font-size="26" text-anchor="middle" fill="#f8fafc">{tiger.code} · {tiger.name or 'Pench Individual'}</text>
      <text x="300" y="315" font-family="monospace" font-size="14" text-anchor="middle" fill="#10b981">{tiger.status.value} · {tiger.total_observations} Sightings · Core Reserve</text>
    </svg>"""
    return Response(content=svg_badge, media_type="image/svg+xml")


@router.patch("/{tiger_id}")
def update_tiger(tiger_id: uuid.UUID, payload: TigerUpdate, db: Annotated[Session, Depends(get_db)]):
    """Update tiger details."""
    tiger = db.query(Tiger).filter(Tiger.id == tiger_id).first()
    if not tiger:
        raise HTTPException(status_code=404, detail="Tiger not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tiger, field, value)
    db.commit()
    db.refresh(tiger)
    return _tiger_to_dict(tiger)


@router.post("/{tiger_id}/merge/{target_id}")
def merge_tigers(
    tiger_id: uuid.UUID,
    target_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
):
    """Merge tiger_id INTO target_id (tiger_id becomes MERGED)."""
    source = db.query(Tiger).filter(Tiger.id == tiger_id).first()
    target = db.query(Tiger).filter(Tiger.id == target_id).first()
    if not source or not target:
        raise HTTPException(status_code=404, detail="Tiger not found")
    if source.id == target.id:
        raise HTTPException(status_code=400, detail="Cannot merge a tiger into itself")

    # Reassign observations
    db.query(Observation).filter(Observation.tiger_id == tiger_id).update(
        {Observation.tiger_id: target_id}
    )
    # Update stats
    target.total_observations += source.total_observations
    if source.first_seen and (not target.first_seen or source.first_seen < target.first_seen):
        target.first_seen = source.first_seen
    if source.last_seen and (not target.last_seen or source.last_seen > target.last_seen):
        target.last_seen = source.last_seen

    source.status = TigerStatus.MERGED
    source.merged_into_id = target_id
    db.commit()
    return {"merged": str(tiger_id), "into": str(target_id), "status": "complete"}
