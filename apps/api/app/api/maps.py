"""GeoJSON endpoints for map visualization."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.observation import Observation
from app.models.station import Station

router = APIRouter(prefix="/maps", tags=["spatial intelligence"])


@router.get("/stations.geojson")
@router.get("/stations")
def stations_geojson(db: Annotated[Session, Depends(get_db)]):
    """Return all stations as GeoJSON FeatureCollection."""
    stations = db.query(Station).all()
    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [s.longitude, s.latitude],
            },
            "properties": {
                "id": str(s.id),
                "code": s.code,
                "name": s.name,
                "zone": s.zone.value if hasattr(s.zone, "value") else str(s.zone),
                "status": s.status.value if hasattr(s.status, "value") else str(s.status),
            },
        }
        for s in stations
    ]
    return {
        "data_notice": "DEMONSTRATION DATA",
        "type": "FeatureCollection",
        "features": features,
    }


@router.get("/observations.geojson")
@router.get("/observations")
def observations_geojson(db: Annotated[Session, Depends(get_db)]):
    """Return observations as GeoJSON FeatureCollection."""
    observations = (
        db.query(Observation)
        .join(Station, Observation.station_id == Station.id)
        .all()
    )
    features = []
    for obs in observations:
        station = obs.station
        if station:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [station.longitude, station.latitude],
                },
                "properties": {
                    "id": str(obs.id),
                    "tiger_id": str(obs.tiger_id),
                    "station_id": str(obs.station_id),
                    "station_code": station.code,
                    "identity_confidence": obs.identity_confidence,
                    "captured_at": obs.captured_at.isoformat(),
                    "synthetic": True,
                },
            })
    return {
        "data_notice": "DEMONSTRATION DATA",
        "type": "FeatureCollection",
        "features": features,
    }


@router.get("/sightseeing.geojson")
@router.get("/sightseeing")
def sightseeing_geojson():
    """Return tentative sightseeing probability zones."""
    zones = [
        {
            "id": "zone-alikatta",
            "name": "Alikatta Meadow Hotspot",
            "zone_type": "CORE",
            "coordinates": [79.3215, 21.7432],
            "radius_meters": 1200,
            "visibility_score": 94,
            "resident_tigers": ["T017 (Baghira)", "T012 (Collarwali Lineage)"],
            "best_timing": "06:00 AM - 08:30 AM",
        },
        {
            "id": "zone-bodhanala",
            "name": "Bodhanala Reservoir Shore",
            "zone_type": "CORE",
            "coordinates": [79.3042, 21.7318],
            "radius_meters": 1100,
            "visibility_score": 93,
            "resident_tigers": ["T021 (Tara)", "T017 (Baghira)"],
            "best_timing": "16:00 PM - 18:15 PM",
        },
        {
            "id": "zone-gumtara",
            "name": "Gumtara Bamboo Corridor",
            "zone_type": "CORE",
            "coordinates": [79.2654, 21.7125],
            "radius_meters": 1000,
            "visibility_score": 84,
            "resident_tigers": ["T032 (Naina & Cubs)"],
            "best_timing": "06:30 AM - 09:15 AM",
        },
        {
            "id": "zone-chindimatta",
            "name": "Chindimatta High Plateau & Ridge",
            "zone_type": "CORE",
            "coordinates": [79.2876, 21.7556],
            "radius_meters": 1300,
            "visibility_score": 80,
            "resident_tigers": ["T008 (Sheru)", "T045 (Shadow)"],
            "best_timing": "06:15 AM - 08:45 AM",
        },
    ]

    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": z["coordinates"],
            },
            "properties": z,
        }
        for z in zones
    ]

    return {
        "data_notice": "DEMONSTRATION DATA",
        "type": "FeatureCollection",
        "features": features,
    }
