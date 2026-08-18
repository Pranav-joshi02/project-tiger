"""Conservation anomaly detection engine."""
from datetime import datetime, timezone
import uuid
from .scoring import severity


def generate_alerts(features: dict) -> list[dict]:
    events = []
    for event, enabled in (
        ("range_shift", features.get("range_shift")),
        ("new_station", features.get("new_station")),
        ("buffer_entry", features.get("buffer_entry")),
        ("absence", features.get("absence")),
    ):
        if enabled:
            events.append({
                "type": event,
                "severity": severity(float(features.get("confidence", 0.5))),
                "evidence": features.get("evidence", {}),
            })
    return events


def run_alert_engine(tiger_id: str, observations: list[dict]) -> list[dict]:
    """Run alert detection rules on a history of tiger observations.

    observations details format:
      [{"tiger_id": str, "station_id": str, "captured_at": str (ISO), "zone": str ("CORE" | "BUFFER")}]
    """
    alerts = []
    if not observations:
        return alerts

    # Sort observations by captured_at ascending
    sorted_obs = []
    for obs in observations:
        cap_at = obs["captured_at"]
        if isinstance(cap_at, str):
            dt = datetime.fromisoformat(cap_at.replace("Z", "+00:00"))
        else:
            dt = cap_at
        sorted_obs.append({**obs, "_dt": dt})

    sorted_obs.sort(key=lambda x: x["_dt"])

    # 1. Rule: Buffer Entry
    # If the latest observation is in the BUFFER zone
    latest_obs = sorted_obs[-1]
    if latest_obs.get("zone") == "BUFFER":
        alerts.append({
            "type": "BUFFER_MOVEMENT",
            "severity": "CRITICAL",
            "details": f"[RULE: BUFFER_ENTRY] Tiger {tiger_id} detected in the Buffer zone at station {latest_obs['station_id']}.",
            "evidence": {
                "latest_observation": latest_obs["captured_at"],
                "station_id": latest_obs["station_id"],
                "zone": "BUFFER",
            },
        })

    # 2. Rule: Extended Absence
    # If duration between latest observation and current date is > 30 days
    now = datetime.now(timezone.utc)
    delta = now - latest_obs["_dt"]
    if delta.days > 30:
        alerts.append({
            "type": "EXTENDED_ABSENCE",
            "severity": "HIGH",
            "details": f"[RULE: ABSENCE] Tiger {tiger_id} has not been observed for {delta.days} days (threshold: 30 days).",
            "evidence": {
                "last_seen": latest_obs["captured_at"],
                "days_missing": delta.days,
            },
        })

    # 3. Rule: Station Novelty
    # Tiger observed at a station it has never been seen at before (excluding the latest observation itself)
    historical_stations = {o["station_id"] for o in sorted_obs[:-1]}
    latest_station = latest_obs["station_id"]
    if historical_stations and latest_station not in historical_stations:
        alerts.append({
            "type": "STATION_NOVELTY",
            "severity": "MEDIUM",
            "details": f"[RULE: NOVELTY] Tiger {tiger_id} detected at camera station {latest_station} for the first time.",
            "evidence": {
                "new_station_id": latest_station,
                "historical_stations_count": len(historical_stations),
            },
        })

    return alerts

