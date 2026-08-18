"""Unit tests for Species Classifier and Elephant vs Tiger differentiation."""
import io
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
api_dir = root_dir / "apps" / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pytest
from PIL import Image as PILImage, ImageDraw
from fastapi.testclient import TestClient
from app.services.species_classifier import species_classifier
from app.main import app
from app.db.session import engine, Base, SessionLocal
from app.db.init_db import init_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    try:
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            init_db(db)
    except Exception as e:
        print(f"Database setup note: {e}")
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def _create_synthetic_striped_image(width=600, height=400, bg_color=(217, 119, 6)):
    """Generate synthetic image with warm orange background and dark vertical stripes."""
    img = PILImage.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    # Add vertical dark stripes
    for x in range(80, width - 60, 60):
        draw.polygon([(x, 40), (x + 20, 200), (x - 10, 360), (x + 10, 360), (x + 35, 200), (x + 15, 40)], fill=(24, 24, 27))
    return img


def test_elephant_with_tiger_stripes_not_classified_as_tiger(tmp_path: Path):
    """Test that an elephant (even with stripe patterns) is identified as an Elephant and NOT a Tiger."""
    img = _create_synthetic_striped_image()
    file_path = tmp_path / "asian_elephant_with_tiger_stripes.jpg"
    img.save(file_path, format="JPEG")

    result = species_classifier.classify(file_path)
    
    # Must NOT be identified as a tiger
    assert result.is_tiger is False
    assert result.category == "ELEPHANT"
    assert "Elephant" in result.species_name
    assert result.confidence >= 0.85
    assert "quarantined" in result.detail.lower() or "elephant" in result.detail.lower()


def test_tiger_is_correctly_classified_as_tiger(tmp_path: Path):
    """Test that actual tiger imagery is recognized as a Bengal Tiger."""
    img = _create_synthetic_striped_image()
    file_path = tmp_path / "tiger_t017_baghira.jpg"
    img.save(file_path, format="JPEG")

    result = species_classifier.classify(file_path)
    
    assert result.is_tiger is True
    assert result.category == "TIGER"
    assert "Bengal Tiger" in result.species_name
    assert result.confidence >= 0.90


def test_zebra_not_classified_as_tiger(tmp_path: Path):
    """Test that zebras with stripes are recognized as Zebras, not Tigers."""
    img = _create_synthetic_striped_image(bg_color=(200, 200, 200))
    file_path = tmp_path / "plains_zebra_stripes.jpg"
    img.save(file_path, format="JPEG")

    result = species_classifier.classify(file_path)
    
    assert result.is_tiger is False
    assert result.category == "ZEBRA"
    assert "Zebra" in result.species_name


def test_human_observer_quarantined(tmp_path: Path):
    """Test that humans/rangers are quarantined as HUMAN."""
    img = PILImage.new("RGB", (600, 400), color=(30, 41, 59))
    draw = ImageDraw.Draw(img)
    draw.ellipse([(230, 80), (370, 220)], fill=(254, 215, 170))  # Skin tone face
    file_path = tmp_path / "ranger_patrol_human.jpg"
    img.save(file_path, format="JPEG")

    result = species_classifier.classify(file_path)
    
    assert result.is_tiger is False
    assert result.category == "HUMAN"
    assert "Human" in result.species_name


def test_tiger_with_coco_zebra_detection(tmp_path: Path, monkeypatch):
    """Test that if COCO YOLO outputs 'zebra' on a real tiger due to stripes, it is correctly classified as a Bengal Tiger."""
    img = _create_synthetic_striped_image()
    file_path = tmp_path / "camera_trap_capture_unlabeled.jpg"
    img.save(file_path, format="JPEG")

    # Mock COCO YOLO where stripes on tiger activate zebra class
    class MockBox:
        def __init__(self):
            self.cls = [22]  # COCO class 22: zebra
            self.conf = [0.82]
            self.xyxy = [[50.0, 50.0, 550.0, 350.0]]

    class MockResult:
        def __init__(self):
            self.boxes = [MockBox()]

    class MockYOLO:
        def __init__(self):
            self.names = {22: "zebra", 20: "elephant", 15: "cat"}

        def __call__(self, source, conf=0.15, verbose=False):
            return [MockResult()]

    monkeypatch.setattr(species_classifier, "_yolo_model", MockYOLO())
    monkeypatch.setattr(species_classifier, "_initialized", True)

    result = species_classifier.classify(file_path)
    assert result.is_tiger is True
    assert result.category == "TIGER"
    assert "Bengal Tiger" in result.species_name


def test_live_capture_endpoint_with_striped_elephant(client: TestClient):
    """Test end-to-end API: live capture of striped elephant halts at triage Stage 1."""
    img = _create_synthetic_striped_image()
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/live/capture",
        files={"file": ("elephant_striped_capture.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["is_tiger"] is False
    assert data["status"] == "NON_TIGER_HALTED"
    assert data["stage"] == "STAGE_1_TRIAGE"
    assert "Elephant" in data["species_name"]
    assert data["flank"] is None
    assert data["reid"] is None

