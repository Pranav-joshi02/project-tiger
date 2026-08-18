"""Safe, deterministic camera-trap ingestion for the initial MVP.

No raw source is ever deleted. High-confidence blanks are copied into a
quarantine namespace, allowing restoration without touching source evidence.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from shutil import copy2
from uuid import uuid4
from app.services.megadetector import MegaDetectorAdapter

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}

@dataclass
class ImageDecision:
    path: str
    sha256: str
    size_bytes: int
    state: str
    confidence: float
    quarantine_path: str | None = None
    model_version: str | None = None
    detail: str | None = None

@dataclass
class RunRecord:
    id: str
    source_directory: str
    created_at: datetime
    status: str
    images: list[ImageDecision]

class IngestionService:
    def __init__(self, storage_root: Path, detector: MegaDetectorAdapter, blank_threshold: float, subject_threshold: float):
        self.root = storage_root.resolve()
        self.runs: dict[str, RunRecord] = {}
        self.detector, self.blank_threshold, self.subject_threshold = detector, blank_threshold, subject_threshold

    def create_run(self, source_directory: str) -> RunRecord:
        source = (self.root / "raw" / source_directory).resolve()
        raw_root = (self.root / "raw").resolve()
        if not source.is_relative_to(raw_root) or not source.is_dir():
            raise ValueError("Source directory must exist under storage/raw")
        record = RunRecord(str(uuid4()), source_directory, datetime.now(timezone.utc), "processing", [])
        seen_hashes: set[str] = set()
        for image in source.rglob("*"):
            if not image.is_file() or image.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            digest = self._hash(image)
            if digest in seen_hashes:
                record.images.append(ImageDecision(str(image), digest, image.stat().st_size, "DUPLICATE", 1.0))
                continue
            seen_hashes.add(digest)
            triage = self.detector.evaluate(image, self.blank_threshold, self.subject_threshold)
            confidence, state = triage.max_subject_confidence or 0.0, triage.status
            destination = None
            if state == "QUARANTINED":
                destination_path = self.root / "quarantine" / record.id / image.name
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                copy2(image, destination_path)
                destination = str(destination_path)
            record.images.append(ImageDecision(str(image), digest, image.stat().st_size, state, confidence, destination, triage.model_version, triage.detail))
        record.status = "complete"
        self.runs[record.id] = record
        return record

    @staticmethod
    def _hash(path: Path) -> str:
        digest = sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def summary(record: RunRecord) -> dict:
        quarantined = [x for x in record.images if x.state == "QUARANTINED"]
        return {"id":record.id, "status":record.status, "created_at":record.created_at,
          "total_images":len(record.images), "retained_images":sum(x.state == "ACTIVE" for x in record.images),
          "quarantined_images":len(quarantined), "quarantined_bytes":sum(x.size_bytes for x in quarantined),
          "review_required":sum(x.state in {"DUPLICATE", "REVIEW_REQUIRED"} for x in record.images)}
