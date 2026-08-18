"""Comprehensive test script for all Pench Tiger Intelligence APIs.
"""
import sys
from pathlib import Path

# Add paths
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "apps" / "api"))

from fastapi.testclient import TestClient
from app.main import app

def test_all_endpoints():
    print("========================================")
    print("Testing Pench Tiger Intelligence APIs")
    print("========================================")
    client = TestClient(app)

    # 1. Health check
    res = client.get("/health")
    print(f"GET /health -> status: {res.status_code}, data: {res.json()}")
    assert res.status_code == 200

    # 2. Dashboard
    res = client.get("/dashboard")
    print(f"GET /dashboard -> status: {res.status_code}, metrics: {res.json().get('metrics')}")
    assert res.status_code == 200
    assert "metrics" in res.json()

    # 3. Tigers list
    res = client.get("/tigers")
    print(f"GET /tigers -> status: {res.status_code}, count: {res.json().get('total')}")
    assert res.status_code == 200
    tigers = res.json().get("tigers", [])
    assert len(tigers) > 0
    tiger_id = tigers[0]["id"]

    # 4. Tiger detail
    res = client.get(f"/tigers/{tiger_id}")
    print(f"GET /tigers/{tiger_id} -> status: {res.status_code}, code: {res.json().get('code')}")
    assert res.status_code == 200

    # 5. Stations
    res = client.get("/stations")
    print(f"GET /stations -> status: {res.status_code}, count: {len(res.json().get('stations', []))}")
    assert res.status_code == 200

    # 6. Reviews queue
    res = client.get("/reviews")
    print(f"GET /reviews -> status: {res.status_code}, count: {len(res.json().get('reviews', []))}")
    assert res.status_code == 200

    # 7. Alerts
    res = client.get("/alerts")
    print(f"GET /alerts -> status: {res.status_code}, count: {len(res.json().get('alerts', []))}")
    assert res.status_code == 200

    # 8. Observations
    res = client.get("/observations")
    print(f"GET /observations -> status: {res.status_code}, count: {len(res.json().get('observations', []))}")
    assert res.status_code == 200

    # 9. Maps
    res = client.get("/maps/stations.geojson")
    print(f"GET /maps/stations.geojson -> status: {res.status_code}, features: {len(res.json().get('features', []))}")
    assert res.status_code == 200

    res = client.get("/maps/observations.geojson")
    print(f"GET /maps/observations.geojson -> status: {res.status_code}, features: {len(res.json().get('features', []))}")
    assert res.status_code == 200


    # 10. Reports
    res = client.get("/reports/summary")
    print(f"GET /reports/summary -> status: {res.status_code}")
    assert res.status_code == 200

    # 11. Live capture: non-tiger
    import io
    from PIL import Image
    blank_img = Image.new("RGB", (224, 224), color=(34, 139, 34))
    buf = io.BytesIO()
    blank_img.save(buf, format="JPEG")
    buf.seek(0)
    res = client.post(
        "/live/capture",
        files={"file": ("blank.jpg", buf.getvalue(), "image/jpeg")},
        data={"station_code": "STN-001"}
    )
    print(f"POST /live/capture (blank) -> status: {res.status_code}, is_tiger: {res.json().get('is_tiger')}, status: {res.json().get('status')}")
    assert res.status_code == 200
    assert res.json()["is_tiger"] is False

    # 12. Live capture: tiger
    tiger_img = Image.new("RGB", (224, 224), color=(220, 100, 20))
    tbuf = io.BytesIO()
    tiger_img.save(tbuf, format="JPEG")
    tbuf.seek(0)
    res = client.post(
        "/live/capture",
        files={"file": ("tiger.jpg", tbuf.getvalue(), "image/jpeg")},
        data={"station_code": "STN-001"}
    )
    reid_data = res.json().get("reid", {})
    print(f"POST /live/capture (tiger) -> status: {res.status_code}, is_tiger: {res.json().get('is_tiger')}, code: {reid_data.get('tiger_code')}, confidence: {reid_data.get('match_confidence')}")
    assert res.status_code == 200
    assert res.json()["is_tiger"] is True

    # 13. Live capture: same tiger picture repeat test
    tbuf.seek(0)
    res_repeat = client.post(
        "/live/capture",
        files={"file": ("tiger.jpg", tbuf.getvalue(), "image/jpeg")},
        data={"station_code": "STN-001"}
    )
    repeat_reid = res_repeat.json().get("reid", {})
    print(f"POST /live/capture (repeat tiger) -> status: {res_repeat.status_code}, is_same_image: {repeat_reid.get('is_same_image')}, confidence: {repeat_reid.get('match_confidence')}")
    assert res_repeat.status_code == 200
    assert repeat_reid.get("is_same_image") is True
    assert repeat_reid.get("match_confidence") >= 0.99

    print("========================================")
    print("ALL API ENDPOINTS TESTED AND VERIFIED 100%!")
    print("========================================")



if __name__ == "__main__":
    test_all_endpoints()

