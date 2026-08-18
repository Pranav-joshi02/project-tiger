"""Seed the database with synthetic demonstration data.

All data is explicitly labeled as synthetic and must not be used for
conservation operations.
"""
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add API to path (both host and container)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api"))
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, "/srv")


from app.core.config import settings
from app.db.session import SessionLocal, engine, Base
from app.models import *  # noqa: F403


def seed():
    """Seed the database with demo data."""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(Tiger).count() > 0 and db.query(SafariRoute).count() > 0:
            print("Database already seeded with tigers and safari routes. Skipping.")
            return

        print("Seeding database with real Pench Tiger Reserve demonstration data...")
        print("NOTE: All data is synthetic and clearly labelled.")
        print()

        # Create demo user
        from app.core.security import hash_password
        if db.query(User).count() == 0:
            user = User(
                email="riya@pench.gov.in",
                hashed_password=hash_password("demo2026"),
                full_name="Riya Joshi",
                role=UserRole.FOREST_OFFICER,
            )
            db.add(user)
            db.flush()

        # Create reserve
        reserve = db.query(Reserve).filter(Reserve.code == "PENCH").first()
        if not reserve:
            reserve = Reserve(
                name="Pench Tiger Reserve",
                code="PENCH",
            )
            db.add(reserve)
            db.flush()

        # Create stations (Real Pench Coordinates)
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
            existing_stn = db.query(Station).filter(Station.code == code).first()
            if not existing_stn:
                station = Station(
                    code=code,
                    name=name,
                    latitude=lat,
                    longitude=lon,
                    zone=StationZone(zone),
                    status=StationStatus.ACTIVE if code != "CT-09" else StationStatus.MAINTENANCE,
                    reserve_id=reserve.id,
                )
                db.add(station)
                db.flush()
                station_map[code] = station
            else:
                station_map[code] = existing_stn

        # Create tigers
        tigers_data = [
            ("T017", "Baghira", "MALE", "CONFIRMED", 18),
            ("T021", "Tara", "FEMALE", "CONFIRMED", 14),
            ("T008", "Sheru", "MALE", "CONFIRMED", 27),
            ("T032", "Naina", "FEMALE", "CONFIRMED", 11),
            ("T045", "Shadow", "MALE", "CONFIRMED", 19),
            ("T012", "Collarwali Lineage", "FEMALE", "CONFIRMED", 16),
        ]
        tiger_map = {}
        for code, name, sex, status, obs_count in tigers_data:
            existing_tiger = db.query(Tiger).filter(Tiger.code == code).first()
            if not existing_tiger:
                tiger = Tiger(
                    code=code,
                    name=name,
                    sex=TigerSex(sex),
                    status=TigerStatus(status),
                    reserve_id=reserve.id,
                    total_observations=obs_count,
                    first_seen=datetime(2025, 1, 1, tzinfo=timezone.utc),
                    last_seen=datetime(2026, 8, 15, tzinfo=timezone.utc),
                )
                db.add(tiger)
                db.flush()
                tiger_map[code] = tiger
            else:
                tiger_map[code] = existing_tiger

        # Seed Sightseeing Zones
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
                "description": "The premier wildlife viewing meadow in Pench. Expansive open vistas with high density of spotted deer, gaur, and resident tigers.",
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
                "description": "Perennial water reservoir where resident tigress Tara and male Baghira frequently cool off during warm afternoons.",
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
                "description": "Stark white Kulu ghost trees contrasting against teak forests with marshy springs attracting tigress T012.",
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
            existing_zone = db.query(SightseeingZone).filter(SightseeingZone.code == z["code"]).first()
            if not existing_zone:
                zone_obj = SightseeingZone(**z)
                db.add(zone_obj)
        db.flush()

        # Seed Safari Routes & Waypoints
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
            existing_route = db.query(SafariRoute).filter(SafariRoute.code == r_data["code"]).first()
            if not existing_route:
                route_obj = SafariRoute(**r_data)
                db.add(route_obj)
                db.flush()
                for wp in wps:
                    wp_obj = SafariWaypoint(route_id=route_obj.id, **wp)
                    db.add(wp_obj)

        # Seed Initial Real-Time Sightings
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

        db.commit()
        print("\nSeeding complete!")
        print(f"  Stations: {len(stations_data)}")
        print(f"  Tigers: {len(tigers_data)}")
        print(f"  Sightseeing Zones: {len(zones_data)}")
        print(f"  Safari Routes: {len(routes_data)}")
        print(f"  Sightings Logged: {len(sightings_data)}")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
