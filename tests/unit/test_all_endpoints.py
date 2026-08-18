"""Comprehensive test suite for all Pench Tiger Intelligence API endpoints."""
import sys
from pathlib import Path

# Add apps/api and root to sys.path
root_dir = Path(__file__).resolve().parents[2]
api_dir = root_dir / "apps" / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import engine, Base, SessionLocal
from app.db.init_db import init_db

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        init_db(db)
    yield

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_health_endpoints(client: TestClient):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("ok", "degraded")
    assert "database" in data

def test_dashboard_endpoint(client: TestClient):
    res = client.get("/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "metrics" in data
    assert "alerts" in data
    assert data["metrics"]["known_individuals"] >= 1

def test_tigers_endpoints(client: TestClient):
    # 1. List tigers
    res = client.get("/tigers")
    assert res.status_code == 200
    data = res.json()
    assert "tigers" in data
    assert len(data["tigers"]) >= 1

    # 2. Get specific tiger
    first_tiger = data["tigers"][0]
    res = client.get(f"/tigers/{first_tiger['id']}")
    assert res.status_code == 200
    t_data = res.json()
    assert t_data["code"] == first_tiger["code"]

    # 3. Create new tiger
    test_code = "T_TEST_99"
    res = client.post("/tigers", json={
        "code": test_code,
        "name": "Test Tiger",
        "sex": "MALE",
        "notes": "Automated test tiger"
    })
    assert res.status_code in (201, 409)

def test_safari_endpoints(client: TestClient):
    # 1. Routes
    res = client.get("/safari/routes")
    assert res.status_code == 200
    routes = res.json()
    assert isinstance(routes, list)
    assert len(routes) >= 1
    assert "waypoints" in routes[0]

    # 2. Sightseeing Zones
    res = client.get("/safari/zones")
    assert res.status_code == 200
    zones = res.json()
    assert isinstance(zones, list)
    assert len(zones) >= 1

    # 3. Dynamic Tiger Locations
    res = client.get("/safari/tiger-locations")
    assert res.status_code == 200
    locations = res.json()
    assert isinstance(locations, list)
    assert len(locations) >= 1
    assert "latitude" in locations[0]
    assert "longitude" in locations[0]
    assert "recent_coordinates" in locations[0]

    # 4. Geocode
    res = client.get("/safari/geocode?q=Alikatta")
    assert res.status_code == 200
    geo = res.json()
    assert "latitude" in geo
    assert "longitude" in geo
    assert "Alikatta" in geo["matched_landmark"]

    # 5. Spot and Plot Tiger
    res = client.post("/safari/spot-tiger", json={
        "tiger_code": "T099",
        "tiger_name": "Kalyani",
        "tiger_sex": "FEMALE",
        "location_name": "Bodhanala Reservoir Shore",
        "latitude": 21.7318,
        "longitude": 79.3042,
        "behavior": "Drinking water at shore",
        "confidence_score": 0.98,
        "observed_by": "GYPSY_NATURALIST"
    })
    assert res.status_code == 200
    spot_data = res.json()
    assert spot_data["status"] == "SUCCESS"
    assert spot_data["sighting"]["tiger_code"] == "T099"
    assert spot_data["tiger"]["code"] == "T099"

    # 6. Verify sightings list has new sighting
    res = client.get("/safari/sightings")
    assert res.status_code == 200
    sightings = res.json()
    assert isinstance(sightings, list)
    assert any(s["tiger_code"] == "T099" for s in sightings)

def test_stations_endpoint(client: TestClient):
    res = client.get("/stations")
    assert res.status_code == 200
    data = res.json()
    assert "stations" in data or isinstance(data, list)

def test_alerts_endpoints(client: TestClient):
    res = client.get("/alerts")
    assert res.status_code == 200
    data = res.json()
    assert "alerts" in data or isinstance(data, list)

def test_reviews_endpoint(client: TestClient):
    res = client.get("/reviews")
    assert res.status_code == 200
    data = res.json()
    assert "reviews" in data or isinstance(data, list)

def test_maps_endpoint(client: TestClient):
    res = client.get("/maps/stations.geojson")
    assert res.status_code == 200
    res = client.get("/maps/sightseeing.geojson")
    assert res.status_code == 200
    res = client.get("/maps/observations.geojson")
    assert res.status_code == 200
