"""Test live image upload and Re-ID matching pipeline."""
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
from PIL import Image as PILImage
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

def test_live_image_upload_pipeline(client: TestClient):
    # Create a synthetic image in memory
    img = PILImage.new("RGB", (640, 480), color=(180, 100, 40))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    # Post to live capture endpoint
    response = client.post(
        "/live/capture",
        files={"file": ("test_tiger_field_photo.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "stage" in data
    assert data["status"] in ("TIGER_IDENTIFIED", "AUTO_MATCH", "REVIEW_REQUIRED", "NEW_TIGER", "NON_TIGER_HALTED")
    assert "run_id" in data
