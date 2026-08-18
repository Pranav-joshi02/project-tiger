"""Database initialization and automatic seed routine for Docker & local deployments."""
import logging
import hashlib
import numpy as np
from datetime import datetime, timezone, timedelta
import sqlalchemy as sa
from app.db.session import engine, Base
from app.models import (
    User, UserRole,
    Reserve,
    Station, StationZone, StationStatus,
    Tiger, TigerSex, TigerStatus,
    Observation,
    Alert, AlertType, AlertSeverity, AlertStatus,
    Run, RunStatus,
    Review, ReviewState,
    SafariRoute, SafariWaypoint, SightseeingZone, SafariSighting,
    SafariZone, WaypointType, ObserverType,
    Embedding,
)

logger = logging.getLogger(__name__)


def init_db(db):
    """Ensure all tables are created and demo dataset is seeded if empty."""
    # Ensure extensions safely
    with engine.connect() as conn:
        for ext in ["uuid-ossp", "postgis", "vector"]:
            try:
                conn.execute(sa.text(f'CREATE EXTENSION IF NOT EXISTS "{ext}";'))
                conn.commit()
            except Exception as e:
                pass

    Base.metadata.create_all(bind=engine)

    # Check if tigers exist
    tiger_count = db.query(Tiger).count()

    if tiger_count >= 6:
        logger.info(f"Database already populated ({tiger_count} tigers). Skipping seed.")
        return

    logger.info("Auto-seeding PostgreSQL database with real Pench Tiger Reserve demonstration data...")

    # 1. Create demo user
    from app.core.security import hash_password
    user = db.query(User).filter(User.email == "riya@pench.gov.in").first()
    if not user:
        user = User(
            email="riya@pench.gov.in",
            hashed_password=hash_password("demo2026"),
            full_name="Riya Joshi",
            role=UserRole.FOREST_OFFICER,
        )
        db.add(user)
        db.flush()

    # 2. Create Reserve
    reserve = db.query(Reserve).filter(Reserve.code == "PENCH").first()
    if not reserve:
        reserve = Reserve(
            name="Pench Tiger Reserve",
            code="PENCH",
        )
        db.add(reserve)
        db.flush()

    # 3. Create Stations (Real Pench GIS Coordinates)
    stations_data = [
        ("CT-01", "Alikatta Central Meadow", 21.7432, 79.3215, "CORE"),
        ("CT-02", "Bodhanala Crossing", 21.7318, 79.3042, "CORE"),
        ("CT-03", "Chindimatta Ridge Overlook", 21.7556, 79.2876, "CORE"),
        ("CT-04", "Dudhgaon Grassland Trail", 21.7681, 79.3398, "CORE"),
        ("CT-05", "Gumtara Bamboo Waterhole", 21.7125, 79.2654, "CORE"),
        ("CT-06", "Jamuntola Bamboo", 21.7890, 79.3101, "BUFFER"),
        ("CT-07", "Karmajhiri Buffer Gate", 21.6901, 79.2888, "BUFFER"),
        ("CT-08", "Pyorthadi Ghost Tree Spring", 21.7240, 79.3360, "CORE"),
        ("CT-09", "Raipur Grassland", 21.7645, 79.2723, "BUFFER"),
        ("CT-10", "Touria Gate East Checkpost", 21.7000, 79.3100, "BUFFER"),
    ]
    station_map = {}
    for code, name, lat, lon, zone in stations_data:
        stn = db.query(Station).filter(Station.code == code).first()
        if not stn:
            stn = Station(
                code=code,
                name=name,
                latitude=lat,
                longitude=lon,
                zone=StationZone(zone),
                status=StationStatus.ACTIVE if code != "CT-09" else StationStatus.MAINTENANCE,
                reserve_id=reserve.id,
            )
            db.add(stn)
            db.flush()
        station_map[code] = stn

    # 4. Create Tigers
    tigers_data = [
        ("T017", "Baghira", "MALE", "CONFIRMED", 18, "Dominant prime male inhabiting Alikatta grasslands and Bodhanala core."),
        ("T021", "Tara", "FEMALE", "CONFIRMED", 14, "Resident female frequently spotted along Bodhanala stream and Baghin Nala."),
        ("T008", "Sheru", "MALE", "CONFIRMED", 27, "Veteran alpha male holding the high-elevation Chindimatta plateau and Totladoh ridge."),
        ("T032", "Naina", "FEMALE", "CONFIRMED", 11, "Young mother with 2 sub-adult cubs patrolling Gumtara bamboo dense nullahs."),
        ("T045", "Shadow", "MALE", "CONFIRMED", 19, "Stealth male active in southern core-buffer corridor near Karmajhiri and Rukhad."),
        ("T012", "Collarwali Lineage", "FEMALE", "CONFIRMED", 16, "Direct daughter of legendary matriarch, rules eastern Touria and Pyorthadi waterbody."),
    ]
    tiger_map = {}
    for code, name, sex, status, obs_count, notes in tigers_data:
        t = db.query(Tiger).filter(Tiger.code == code).first()
        if not t:
            t = Tiger(
                code=code,
                name=name,
                sex=TigerSex(sex),
                status=TigerStatus(status),
                reserve_id=reserve.id,
                total_observations=obs_count,
                confirmed_observations=obs_count,
                notes=notes,
                first_seen=datetime(2025, 1, 1, tzinfo=timezone.utc),
                last_seen=datetime.now(timezone.utc),
            )
            db.add(t)
            db.flush()

            # Seed Left & Right prototype embeddings if vector support available
            try:
                np.random.seed(int(hashlib.md5(code.encode()).hexdigest()[:8], 16) % (2**31))
                vec_left = np.random.randn(512).astype(np.float32)
                vec_left = (vec_left / np.linalg.norm(vec_left)).tolist()

                vec_right = np.random.randn(512).astype(np.float32)
                vec_right = (vec_right / np.linalg.norm(vec_right)).tolist()

                emb_l = Embedding(
                    tiger_id=t.id,
                    vector=vec_left,
                    model_version="convnext-small-v1",
                    side="LEFT",
                    quality_weight=0.95,
                    is_prototype=True,
                    confirmed=True,
                )
                emb_r = Embedding(
                    tiger_id=t.id,
                    vector=vec_right,
                    model_version="convnext-small-v1",
                    side="RIGHT",
                    quality_weight=0.95,
                    is_prototype=True,
                    confirmed=True,
                )
                db.add(emb_l)
                db.add(emb_r)
                db.flush()
                t.left_prototype_id = emb_l.id
                t.right_prototype_id = emb_r.id
                db.flush()
            except Exception as e:
                logger.info(f"Skipped prototype embeddings for {code}: {e}")

        tiger_map[code] = t

    # 5. Create Sightseeing Zones
    zones_data = [
        {
            "code": "zone-alikatta",
            "name": "Alikatta Meadow Hotspot",
            "zone_type": "CORE",
            "latitude": 21.7432,
            "longitude": 79.3215,
            "radius_meters": 1200,
            "visibility_score_morning": 94,
            "visibility_score_afternoon": 88,
            "visibility_score_night": 40,
            "primary_habitat": "Open Savanna Grasslands & Central Waterhole",
            "description": "The premier wildlife viewing meadow in Pench with high density of spotted deer and resident tigers.",
            "resident_tigers": ["T017 (Baghira)", "T012 (Collarwali Lineage)", "T021 (Tara)"],
            "key_landmarks": ["Alikatta Watchtower", "Central Salt Lick", "Chital Grass Flats"],
            "recommended_gate": "Touria Gate (14 km drive)",
            "best_safari_timing": "06:00 AM - 08:30 AM",
        },
        {
            "code": "zone-bodhanala",
            "name": "Bodhanala Reservoir Shore",
            "zone_type": "CORE",
            "latitude": 21.7318,
            "longitude": 79.3042,
            "radius_meters": 1100,
            "visibility_score_morning": 86,
            "visibility_score_afternoon": 93,
            "visibility_score_night": 52,
            "primary_habitat": "Perennial Reservoir & Riparian Bamboo Edge",
            "description": "Perennial water reservoir where resident tigress Tara and male Baghira frequently cool off.",
            "resident_tigers": ["T021 (Tara)", "T017 (Baghira)"],
            "key_landmarks": ["Bodhanala Bund Track", "Sunset Point", "Old Causeway"],
            "recommended_gate": "Touria Gate / Karmajhiri Gate",
            "best_safari_timing": "16:00 PM - 18:15 PM",
        },
        {
            "code": "zone-pyorthadi",
            "name": "Pyorthadi Ghost Tree Basin",
            "zone_type": "CORE",
            "latitude": 21.7240,
            "longitude": 79.3360,
            "radius_meters": 950,
            "visibility_score_morning": 89,
            "visibility_score_afternoon": 91,
            "visibility_score_night": 45,
            "primary_habitat": "Ghost Tree (Kulu) Forest & Spring Marsh",
            "description": "Stark white Kulu ghost trees contrasting against teak forests with marshy springs.",
            "resident_tigers": ["T012 (Collarwali Lineage)", "T017 (Baghira)"],
            "key_landmarks": ["Giant Ghost Tree Clump", "Pyorthadi Dam Wall"],
            "recommended_gate": "Touria Gate",
            "best_safari_timing": "15:45 PM - 18:00 PM",
        },
        {
            "code": "zone-gumtara",
            "name": "Gumtara Bamboo & Stream Nullah",
            "zone_type": "CORE",
            "latitude": 21.7125,
            "longitude": 79.2654,
            "radius_meters": 1000,
            "visibility_score_morning": 84,
            "visibility_score_afternoon": 81,
            "visibility_score_night": 65,
            "primary_habitat": "Dense Bamboo & Shaded Nullahs",
            "description": "Home territory of tigress Naina (T032) and her cubs.",
            "resident_tigers": ["T032 (Naina & Cubs)", "T021 (Tara)"],
            "key_landmarks": ["Gumtara Water Tank", "Bamboo Tunnel Track"],
            "recommended_gate": "Gumtara Gate (Direct Entry)",
            "best_safari_timing": "06:30 AM - 09:15 AM",
        },
        {
            "code": "zone-chindimatta",
            "name": "Chindimatta High Plateau & Ridge",
            "zone_type": "CORE",
            "latitude": 21.7556,
            "longitude": 79.2876,
            "radius_meters": 1300,
            "visibility_score_morning": 78,
            "visibility_score_afternoon": 80,
            "visibility_score_night": 72,
            "primary_habitat": "Elevated Rocky Ridge overlooking Totladoh Lake",
            "description": "The rugged territory of alpha male Sheru (T008) overlooking the Pench reservoir.",
            "resident_tigers": ["T008 (Sheru)", "T045 (Shadow)"],
            "key_landmarks": ["Chindimatta Viewpoint", "Totladoh Reservoir Shore"],
            "recommended_gate": "Karmajhiri Gate / Touria Gate",
            "best_safari_timing": "06:15 AM - 08:45 AM",
        },
    ]
    for z in zones_data:
        if not db.query(SightseeingZone).filter(SightseeingZone.code == z["code"]).first():
            db.add(SightseeingZone(**z))
    db.flush()

    # 6. Create Safari Routes & Waypoints
    routes_data = [
        {
            "code": "PTR-SR-01",
            "name": "Touria - Alikatta Prime Core Circuit",
            "zone": SafariZone.TOURIA,
            "gate_name": "Touria Core Gate",
            "visibility_rating": 94,
            "distance_km": 28.5,
            "duration_hours": 3.5,
            "terrain_difficulty": "EASY",
            "slot_recommendation": "BOTH",
            "max_vehicles": 30,
            "current_vehicles_booked": 27,
            "summary": "Pench's highest-probability tiger safari circuit, covering Alikatta meadows, Bodhanala reservoir, and Pyorthadi marsh.",
            "highlights": [
                "94% historical tiger encounter rate across last 30 days",
                "Open grassland landscape ideal for wildlife photography",
                "Prime crossing for dominant male T017 (Baghira)",
            ],
            "resident_tigers": ["T017 (Baghira)", "T021 (Tara)", "T012 (Collarwali Lineage)"],
            "naturalist_tips": "Pause at Alikatta banyan junction between 06:45 - 07:30 AM; listen for alarm calls from sambar herds near the reservoir bund.",
            "suggested_lens": "70-200mm f/2.8 & 100-400mm (Excellent open lighting)",
            "waypoints": [
                {"name": "Touria Entry Gate", "latitude": 21.7000, "longitude": 79.3100, "order": 1, "type": WaypointType.GATE, "tiger_sighting_chance": 20, "description": "Official entry checkpost."},
                {"name": "Baghin Nala Culvert", "latitude": 21.7200, "longitude": 79.3150, "order": 2, "type": WaypointType.RIVERBED, "tiger_sighting_chance": 72, "description": "Seasonal riverbed with frequent pugmarks."},
                {"name": "Alikatta Central Meadow", "latitude": 21.7432, "longitude": 79.3215, "order": 3, "type": WaypointType.MEADOW, "tiger_sighting_chance": 94, "description": "Prime predator-prey grassland hotspot."},
                {"name": "Bodhanala Lake Bund", "latitude": 21.7318, "longitude": 79.3042, "order": 4, "type": WaypointType.WATERHOLE, "tiger_sighting_chance": 88, "description": "Perennial reservoir shoreline."},
                {"name": "Pyorthadi Ghost Tree Clump", "latitude": 21.7240, "longitude": 79.3360, "order": 5, "type": WaypointType.MEADOW, "tiger_sighting_chance": 85, "description": "Marshy spring with high tigress T012 activity."},
            ]
        },
        {
            "code": "PTR-SR-02",
            "name": "Karmajhiri - Chindimatta Riverbed Trail",
            "zone": SafariZone.KARMAJHIRI,
            "gate_name": "Karmajhiri Gate",
            "visibility_rating": 86,
            "distance_km": 34.0,
            "duration_hours": 4.0,
            "terrain_difficulty": "MODERATE",
            "slot_recommendation": "DAWN_SAFARI",
            "max_vehicles": 20,
            "current_vehicles_booked": 16,
            "summary": "Deep wilderness trail exploring rocky ridges, teak valleys, and the dramatic Chindimatta plateau overlooking Totladoh.",
            "highlights": [
                "Alpha male T008 territory with frequent road-patrolling sightings",
                "Spectacular landscape photography across Totladoh reservoir",
            ],
            "resident_tigers": ["T008 (Sheru)", "T045 (Shadow)"],
            "naturalist_tips": "Scan high rocky ledges along Chindimatta for Sheru resting in shade; check Seoni stream bed for fresh morning pugmarks.",
            "suggested_lens": "200-600mm f/5.6-6.3",
            "waypoints": [
                {"name": "Karmajhiri Entry Gate", "latitude": 21.6901, "longitude": 79.2888, "order": 1, "type": WaypointType.GATE, "tiger_sighting_chance": 30, "description": "Northern access point."},
                {"name": "Seoni Stream Nullah", "latitude": 21.7250, "longitude": 79.2820, "order": 2, "type": WaypointType.RIVERBED, "tiger_sighting_chance": 78, "description": "Shaded water course."},
                {"name": "Chindimatta Viewpoint", "latitude": 21.7556, "longitude": 79.2876, "order": 3, "type": WaypointType.RIDGE, "tiger_sighting_chance": 86, "description": "High rocky promontory."},
            ]
        },
        {
            "code": "PTR-SR-03",
            "name": "Gumtara - Ghost Tree Waterhole Loop",
            "zone": SafariZone.GUMTARA,
            "gate_name": "Gumtara Gate",
            "visibility_rating": 82,
            "distance_km": 24.2,
            "duration_hours": 3.0,
            "terrain_difficulty": "EASY",
            "slot_recommendation": "BOTH",
            "max_vehicles": 16,
            "current_vehicles_booked": 11,
            "summary": "Secluded western circuit renowned for bamboo corridors and tigress Naina with her growing cubs.",
            "highlights": ["82% visibility score with high likelihood of cub sightings", "Peaceful game drives with low vehicular density"],
            "resident_tigers": ["T032 (Naina & Cubs)", "T021 (Tara)"],
            "naturalist_tips": "Drive slowly through Bamboo Tunnel Track at 10-15 km/h; tigress Naina often uses the dirt road as a nursery trail.",
            "suggested_lens": "70-200mm & 300mm f/4",
            "waypoints": [
                {"name": "Gumtara Gate Checkpost", "latitude": 21.7050, "longitude": 79.2550, "order": 1, "type": WaypointType.GATE, "tiger_sighting_chance": 22, "description": "Western portal."},
                {"name": "Bamboo Tunnel Track", "latitude": 21.7125, "longitude": 79.2654, "order": 2, "type": WaypointType.MEADOW, "tiger_sighting_chance": 84, "description": "Arching bamboo grove."},
                {"name": "Gumtara Water Tank", "latitude": 21.7190, "longitude": 79.2710, "order": 3, "type": WaypointType.WATERHOLE, "tiger_sighting_chance": 80, "description": "Main waterhole."},
            ]
        }
    ]
    for r_data in routes_data:
        wps = r_data.pop("waypoints")
        r_obj = db.query(SafariRoute).filter(SafariRoute.code == r_data["code"]).first()
        if not r_obj:
            r_obj = SafariRoute(**r_data)
            db.add(r_obj)
            db.flush()
            for wp in wps:
                wp_obj = SafariWaypoint(route_id=r_obj.id, **wp)
                db.add(wp_obj)

    # 7. Initial Sightings
    sightings_data = [
        ("T017", "Baghira", "Alikatta Central Meadow, Culvert 4", 21.7445, 79.3230, "Walking along main dirt road toward Bodhanala; spray marked teak tree.", 0.98, ObserverType.GYPSY_NATURALIST, 25),
        ("T021", "Tara", "Bodhanala Reservoir Shore", 21.7310, 79.3035, "Resting in shaded water shallows to escape heat. Highly visible from main safari track.", 0.95, ObserverType.TOURIST_GROUP, 55),
        ("T032", "Naina", "Gumtara Bamboo Nullah", 21.7135, 79.2660, "Observed leading 2 healthy cubs across stream bed toward thick bamboo cover.", 0.92, ObserverType.FOREST_GUARD, 110),
        ("T008", "Sheru", "Chindimatta High Ridge", 21.7556, 79.2876, "Station CT-03 captured full right-flank profile during morning territory patrol.", 0.94, ObserverType.CAMERA_TRAP, 170),
    ]
    for t_code, t_name, loc, lat, lon, beh, conf, obs_by, mins_ago in sightings_data:
        s_obj = SafariSighting(
            tiger_id=tiger_map[t_code].id if t_code in tiger_map else None,
            tiger_code=t_code,
            tiger_name=t_name,
            location_name=loc,
            latitude=lat,
            longitude=lon,
            behavior=beh,
            confidence_score=conf,
            observed_by=obs_by,
            captured_at=datetime.now(timezone.utc) - timedelta(minutes=mins_ago),
        )
        db.add(s_obj)

    # 8. Initial Alerts
    alerts_data = [
        ("T045", "BUFFER_MOVEMENT", "CRITICAL", "Buffer Zone Peripheral Breach",
         "Tiger T045 (Shadow) verified 1.2 km outside core boundary near Karmajhiri agricultural edge.", 21.6890, 79.2895),
        ("T017", "NEW_TERRITORY", "HIGH", "Dominant Male Territory Expansion",
         "GPS telemetry indicates T017 (Baghira) and T008 (Sheru) within 450m proximity near Bodhanala Ridge.", 21.7445, 79.3230),
        ("T032", "STATION_NOVELTY", "HIGH", "New Station Detection: Tigress with Cubs",
         "Tiger T032 (Naina) detected for the first time at camera station CT-05 with 2 healthy cubs.", 21.7135, 79.2660),
    ]
    for tiger_code, alert_type, severity, title, summary, lat, lon in alerts_data:
        alert = Alert(
            tiger_id=tiger_map[tiger_code].id if tiger_code in tiger_map else None,
            type=AlertType(alert_type),
            severity=AlertSeverity(severity),
            status=AlertStatus.ACTIVE,
            title=title,
            summary=summary,
            evidence={"latitude": lat, "longitude": lon},
        )
        db.add(alert)

    db.commit()
    logger.info("Database auto-seed completed successfully.")
