import sys
from pathlib import Path
from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api"))
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from app.main import app

def create_samples():
    sample_dir = PROJECT_ROOT / "storage" / "test_samples"
    sample_dir.mkdir(parents=True, exist_ok=True)

    # 1. Tiger image (orange with black vertical stripes pattern)
    tiger_img = Image.new("RGB", (640, 480), color=(220, 110, 20))
    draw = ImageDraw.Draw(tiger_img)
    # Draw tiger stripes
    for x in range(60, 580, 40):
        draw.polygon([(x, 80), (x + 15, 200), (x - 10, 360), (x + 5, 420), (x - 5, 420), (x - 25, 200), (x - 10, 80)], fill=(20, 15, 10))
    # Draw tiger facial mark / eye
    draw.ellipse([(140, 120), (170, 150)], fill=(240, 220, 100))
    draw.ellipse([(150, 130), (160, 140)], fill=(10, 10, 10))
    tiger_path = sample_dir / "tiger_baghira_sample.jpg"
    tiger_img.save(tiger_path, quality=95)

    # 2. Forest blank
    blank_img = Image.new("RGB", (640, 480), color=(30, 70, 40))
    draw = ImageDraw.Draw(blank_img)
    for _ in range(50):
        draw.line([(100, 100), (200, 400)], fill=(20, 50, 30), width=4)
    blank_path = sample_dir / "forest_blank.jpg"
    blank_img.save(blank_path, quality=95)

    return tiger_path, blank_path

def test_full_pipeline():
    tiger_path, blank_path = create_samples()
    client = TestClient(app)

    print("--- Test 1: Upload Non-Tiger (Forest Blank) ---")
    with open(blank_path, "rb") as f:
        r = client.post("/live/capture", files={"file": ("forest_blank.jpg", f, "image/jpeg")})
        res = r.json()
        print("Status:", r.status_code)
        print("Is Tiger:", res.get("is_tiger"))
        print("Triage Category:", res.get("triage_category"))
        print("Triage Confidence:", f"{res.get('triage_confidence', 0)*100:.1f}%")
        print("Message:", res.get("message"))
        assert res["is_tiger"] is False

    print("\n--- Test 2: Upload Tiger (First Submission) ---")
    with open(tiger_path, "rb") as f:
        r = client.post("/live/capture", files={"file": ("tiger_baghira_sample.jpg", f, "image/jpeg")})
        res = r.json()
        print("Status:", r.status_code)
        print("Is Tiger:", res.get("is_tiger"))
        print("Triage Category:", res.get("triage_category"))
        print("Triage Confidence:", f"{res.get('triage_confidence', 0)*100:.1f}%")
        print("Flank Side:", res.get("flank", {}).get("side"))
        print("Re-ID Matched Tiger:", res.get("reid", {}).get("tiger_code"), "-", res.get("reid", {}).get("tiger_name"))
        print("Re-ID Match Confidence:", f"{res.get('reid', {}).get('match_confidence', 0)*100:.1f}%")
        assert res["is_tiger"] is True
        assert res.get("reid", {}).get("match_confidence", 0) > 0.80

    print("\n--- Test 3: Upload Same Tiger Picture Again (Repeat Submission) ---")
    with open(tiger_path, "rb") as f:
        r = client.post("/live/capture", files={"file": ("tiger_baghira_sample.jpg", f, "image/jpeg")})
        res = r.json()
        print("Status:", r.status_code)
        print("Is Same Image:", res.get("reid", {}).get("is_same_image"))
        print("Re-ID Matched Tiger:", res.get("reid", {}).get("tiger_code"), "-", res.get("reid", {}).get("tiger_name"))
        print("Re-ID Match Confidence:", f"{res.get('reid', {}).get('match_confidence', 0)*100:.1f}%")
        assert res["is_tiger"] is True
        assert res.get("reid", {}).get("is_same_image") is True
        assert res.get("reid", {}).get("match_confidence", 0) >= 0.99

    print("\nALL MULTI-STAGE TESTS PASSED ACCURATELY!")

if __name__ == "__main__":
    test_full_pipeline()
