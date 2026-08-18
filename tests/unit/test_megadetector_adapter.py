from pathlib import Path
from app.services.megadetector import MegaDetectorAdapter

class FakeDetections:
    confidence = [0.94, 0.31]

class FakeModel:
    def single_image_detection(self, path: str):
        return {"detections": FakeDetections()}

def test_subject_detection_is_retained():
    adapter = MegaDetectorAdapter()
    adapter._model = FakeModel()
    result = adapter.evaluate(Path("camera.jpg"), blank_threshold=.30, subject_threshold=.80)
    assert result.status == "ACTIVE"
    assert result.max_subject_confidence == .94
