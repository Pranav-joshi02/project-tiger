"""Camera station management."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.station import Station, StationStatus, StationZone

router = APIRouter(prefix="/stations", tags=["camera stations"])


class StationCreate(BaseModel):
    code: str
    name: str
    latitude: float
    longitude: float
    zone: StationZone
    elevation_m: float | None = None


def _station_to_dict(station: Station) -> dict:
    return {
        "id": str(station.id),
        "code": station.code,
        "name": station.name,
        "latitude": station.latitude,
        "longitude": station.longitude,
        "zone": station.zone.value,
        "status": station.status.value,
        "elevation_m": station.elevation_m,
        "last_check": station.last_check.isoformat() if station.last_check else None,
        "created_at": station.created_at.isoformat(),
    }


@router.get("")
def list_stations(
    db: Annotated[Session, Depends(get_db)],
    zone: StationZone | None = None,
    status: StationStatus | None = None,
):
    """List all camera stations."""
    query = db.query(Station)
    if zone:
        query = query.filter(Station.zone == zone)
    if status:
        query = query.filter(Station.status == status)
    stations = query.order_by(Station.code).all()
    return {"stations": [_station_to_dict(s) for s in stations], "total": len(stations)}


@router.post("", status_code=201)
def create_station(payload: StationCreate, db: Annotated[Session, Depends(get_db)]):
    """Add a new camera station."""
    existing = db.query(Station).filter(Station.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Station code '{payload.code}' already exists")

    station = Station(
        code=payload.code,
        name=payload.name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        zone=payload.zone,
        elevation_m=payload.elevation_m,
        location={"type": "Point", "coordinates": [payload.longitude, payload.latitude]},
    )
    db.add(station)
    db.commit()
    db.refresh(station)
    return _station_to_dict(station)


@router.get("/{station_id}")
def get_station(station_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):
    """Get station details."""
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    return _station_to_dict(station)


@router.patch("/{station_id}")
def update_station_status(
    station_id: uuid.UUID,
    new_status: StationStatus,
    db: Annotated[Session, Depends(get_db)],
):
    """Update station status."""
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    station.status = new_status
    db.commit()
    return _station_to_dict(station)
