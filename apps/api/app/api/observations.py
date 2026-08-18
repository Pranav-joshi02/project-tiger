"""Observation endpoints with spatial query support."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.observation import Observation

router = APIRouter(prefix="/observations", tags=["observations"])


@router.get("")
def list_observations(
    db: Annotated[Session, Depends(get_db)],
    tiger_id: uuid.UUID | None = None,
    station_id: uuid.UUID | None = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
):
    """List observations with optional filters."""
    query = db.query(Observation)
    if tiger_id:
        query = query.filter(Observation.tiger_id == tiger_id)
    if station_id:
        query = query.filter(Observation.station_id == station_id)
    total = query.count()
    observations = query.order_by(Observation.captured_at.desc()).offset(offset).limit(limit).all()
    return {
        "observations": [
            {
                "id": str(obs.id),
                "tiger_id": str(obs.tiger_id),
                "station_id": str(obs.station_id),
                "identity_confidence": obs.identity_confidence,
                "identity_method": obs.identity_method,
                "flank_side": obs.flank_side,
                "captured_at": obs.captured_at.isoformat(),
                "created_at": obs.created_at.isoformat(),
            }
            for obs in observations
        ],
        "total": total,
    }


@router.get("/{observation_id}")
def get_observation(observation_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    """Get observation details."""
    obs = db.query(Observation).filter(Observation.id == observation_id).first()
    if not obs:
        raise HTTPException(status_code=404, detail="Observation not found")
    return {
        "id": str(obs.id),
        "tiger_id": str(obs.tiger_id),
        "station_id": str(obs.station_id),
        "image_id": str(obs.image_id) if obs.image_id else None,
        "identity_confidence": obs.identity_confidence,
        "identity_method": obs.identity_method,
        "flank_side": obs.flank_side,
        "captured_at": obs.captured_at.isoformat(),
        "created_at": obs.created_at.isoformat(),
    }
