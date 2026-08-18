import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "api"))

from fastapi.testclient import TestClient
from app.main import app

def run_tests():
    client = TestClient(app)
    
    print("Testing /health ...")
    r = client.get("/health")
    print(r.status_code, r.json())
    assert r.status_code == 200

    print("\nTesting /dashboard ...")
    r = client.get("/dashboard")
    print(r.status_code, r.json()["metrics"])
    assert r.status_code == 200

    print("\nTesting /reviews ...")
    r = client.get("/reviews")
    data = r.json()
    print(r.status_code, f"Total reviews: {data['total']}")
    for rev in data["reviews"]:
        print(f"  Review ID: {rev['id'][:8]} | State: {rev['state']} | Candidates: {rev['candidates']}")
    assert r.status_code == 200

    print("\nTesting /tigers ...")
    r = client.get("/tigers")
    tigers = r.json()["tigers"]
    print(r.status_code, f"Total tigers: {len(tigers)}")
    for t in tigers:
        print(f"  {t['code']} - {t['name']} ({t['status']}) - Obs: {t['total_observations']}")
    assert r.status_code == 200

    print("\nTesting /stations ...")
    r = client.get("/stations")
    stations = r.json()["stations"]
    print(r.status_code, f"Total stations: {len(stations)}")
    assert r.status_code == 200

    # Test Live Capture with human/non-tiger image
    print("\nTesting /live/capture with non-tiger image...")
    img_path = Path("storage/raw/live_23e9cddf/live_capture.jpg")
    if img_path.exists():
        with open(img_path, "rb") as f:
            r = client.post("/live/capture", files={"file": ("person_test.jpg", f, "image/jpeg")})
            print("Response:", r.status_code, r.json())
            assert r.json()["is_tiger"] is False

    print("\nALL API ENDPOINTS PASSED WITH FLYING COLORS!")

if __name__ == "__main__":
    run_tests()
