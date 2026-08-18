"""MegaDetector V6 adapter.

The model is intentionally loaded lazily: PytorchWildlife downloads the chosen
V6 weights on first use. A model-load or inference failure is surfaced as a
review-required result; it never turns into an automatic blank decision.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class TriageResult:
    status: str
    max_subject_confidence: float | None
    model_version: str
    detail: str | None = None

class MegaDetectorAdapter:
    def __init__(self, version: str = "MDV6-mit-yolov9-c"):
        self.version = version
        self._model: Any | None = None
        self._load_error: str | None = None

    def evaluate(self, image_path: Path, blank_threshold: float, subject_threshold: float) -> TriageResult:
        try:
            detections = self._detect(image_path)
            scores = self._scores(detections)
        except Exception as error:  # model/network/runtime issue: protect evidence by requiring review
            import logging
            logging.getLogger(__name__).error(f"MegaDetector crashed: {error}", exc_info=True)
            return TriageResult("REVIEW_REQUIRED", None, self.version, f"MegaDetector unavailable: {error}")
        best = max(scores, default=0.0)
        if best >= subject_threshold:
            return TriageResult("ACTIVE", best, self.version)
        if best < blank_threshold:
            return TriageResult("QUARANTINED", best, self.version)
        return TriageResult("REVIEW_REQUIRED", best, self.version, "Confidence lies in the configured review band")

    def _detect(self, image_path: Path) -> Any:
        if self._model is None:
            from PytorchWildlife.models import detection as pw_detection
            # MIT compact V6 is the default; change MEGADETECTOR_VERSION after
            # assessing accuracy, throughput, and licence suitability.
            self._model = pw_detection.MegaDetectorV6(version=self.version)
        return self._model.single_image_detection(str(image_path))

    @staticmethod
    def _scores(result: Any) -> list[float]:
        """Normalize Pytorch-Wildlife/supervision detection confidence outputs."""
        detections = result.get("detections") if isinstance(result, dict) else result
        confidence = getattr(detections, "confidence", None)
        if confidence is None and isinstance(detections, dict): confidence = detections.get("confidence", [])
        if confidence is None: return []
        return [float(value) for value in confidence]
