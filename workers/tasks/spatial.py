"""Spatial analysis task."""
import logging
import uuid
from pathlib import Path

from workers.celery_app import celery_app, get_worker_db

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.spatial.analyze_spatial", queue="spatial")
def analyze_spatial(run_id: str, tiger_ids: list[str] | None = None) -> dict:
    """Run spatial analysis for observed tigers."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))
    from app.models.observation import Observation
    from app.models.station import Station
    from app.models.tiger_range import TigerRange, RangeMethod

    from spatial.mcp import compute_mcp

    db = get_worker_db()
    try:
        if tiger_ids is None:
            # Get all tigers observed in this run
            from app.models.tiger import Tiger
            tiger_ids = [str(t.id) for t in db.query(Tiger).all()]

        results = []
        for tid in tiger_ids:
            observations = (
                db.query(Observation)
                .join(Station)
                .filter(Observation.tiger_id == uuid.UUID(tid))
                .all()
            )

            if len(observations) < 3:
                results.append({"tiger_id": tid, "mcp_computed": False, "reason": "insufficient observations"})
                continue

            points = []
            for obs in observations:
                station = obs.station
                if station:
                    points.append((station.longitude, station.latitude))

            if len(points) >= 3:
                mcp_result = compute_mcp(points)
                if mcp_result.get("valid"):
                    results.append({
                        "tiger_id": tid,
                        "mcp_computed": True,
                        "area_km2": mcp_result["area_km2"],
                    })
                else:
                    results.append({"tiger_id": tid, "mcp_computed": False})
            else:
                results.append({"tiger_id": tid, "mcp_computed": False, "reason": "insufficient points"})

        db.commit()
        logger.info(f"Spatial analysis for run {run_id}: {len(results)} tigers analyzed")
        return {"run_id": run_id, "analyses": results}
    finally:
        db.close()
