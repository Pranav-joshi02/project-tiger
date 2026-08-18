"""Flank quality assessment for tiger Re-ID.

Expanded quality scoring that produces a full QualityVector with per-metric
scores. Quality information is fed INTO the Re-ID model to weight feature
branches, not just used as a pass/fail filter.
"""

try:
    from ml.reid.confidence_model import QualityVector
except ImportError:
    from dataclasses import dataclass
    @dataclass
    class QualityVector:
        blur: float
        exposure: float
        occlusion: float
        visibility: float
        contrast: float
        resolution: float
        composite_score: float

def score(blur: float, visibility: float, occlusion: float) -> float:
    return max(0.0, min(1.0, 0.4 * blur + 0.4 * visibility + 0.2 * (1.0 - occlusion)))

def assess_quality(blur: float, exposure: float, occlusion: float, visibility: float = 1.0, contrast: float = 1.0, resolution: float = 1.0) -> dict:
    composite = max(0.0, min(1.0, 0.3*blur + 0.2*visibility + 0.2*(1.0-occlusion) + 0.1*exposure + 0.1*contrast + 0.1*resolution))
    return {
        "blur": blur,
        "exposure": exposure,
        "occlusion": occlusion,
        "visibility": visibility,
        "contrast": contrast,
        "resolution": resolution,
        "composite_score": composite
    }

def quality_to_vector(blur: float, exposure: float, occlusion: float, visibility: float = 1.0, contrast: float = 1.0, resolution: float = 1.0) -> 'QualityVector':
    scores = assess_quality(blur, exposure, occlusion, visibility, contrast, resolution)
    return QualityVector(**scores)
