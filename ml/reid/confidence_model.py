"""Adaptive confidence calibration and open-set recognition for tiger Re-ID.

Replaces fixed similarity thresholds with a multi-factor confidence model
that considers embedding similarity, image quality, pose compatibility,
visible body area, and occlusion.

Also implements open-set recognition to detect genuinely novel individuals
that don't match any tiger in the database.
"""
from dataclasses import dataclass
import math

@dataclass
class QualityVector:
    blur_score: float = 1.0
    exposure_score: float = 1.0
    contrast_score: float = 1.0
    occlusion_ratio: float = 0.0
    visible_body_pct: float = 1.0
    resolution_score: float = 1.0

    def composite(self) -> float:
        q = (self.blur_score + self.exposure_score + self.contrast_score + self.resolution_score) / 4.0
        q = q * (1.0 - self.occlusion_ratio) * self.visible_body_pct
        return max(0.0, min(1.0, q))

    def to_dict(self) -> dict:
        return {
            "blur_score": self.blur_score,
            "exposure_score": self.exposure_score,
            "contrast_score": self.contrast_score,
            "occlusion_ratio": self.occlusion_ratio,
            "visible_body_pct": self.visible_body_pct,
            "resolution_score": self.resolution_score
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'QualityVector':
        return cls(
            blur_score=d.get("blur_score", 1.0),
            exposure_score=d.get("exposure_score", 1.0),
            contrast_score=d.get("contrast_score", 1.0),
            occlusion_ratio=d.get("occlusion_ratio", 0.0),
            visible_body_pct=d.get("visible_body_pct", 1.0),
            resolution_score=d.get("resolution_score", 1.0)
        )

    @classmethod
    def from_flank_scores(cls, blur: float, exposure: float, occlusion: float) -> 'QualityVector':
        return cls(
            blur_score=blur,
            exposure_score=exposure,
            occlusion_ratio=occlusion,
            contrast_score=1.0,
            visible_body_pct=1.0 - occlusion,
            resolution_score=1.0
        )

class ConfidenceCalibrator:
    def __init__(self, base_match_threshold=0.85, base_review_threshold=0.65, quality_weight=0.15, pose_weight=0.10, visibility_weight=0.10):
        self.base_match_threshold = base_match_threshold
        self.base_review_threshold = base_review_threshold
        self.quality_weight = quality_weight
        self.pose_weight = pose_weight
        self.visibility_weight = visibility_weight

    def calibrate(self, similarity: float, quality: QualityVector, pose_compatibility: float = 1.0) -> float:
        Q = quality.composite()
        P = pose_compatibility
        V = quality.visible_body_pct
        
        calibrated = similarity * (1 + self.quality_weight * (Q - 0.5)) * (1 + self.pose_weight * (P - 0.5)) * (1 + self.visibility_weight * (V - 0.5))
        return max(0.0, min(1.0, calibrated))

    def classify(self, calibrated_confidence: float) -> str:
        if calibrated_confidence >= self.base_match_threshold:
            return 'AUTO_MATCH'
        elif calibrated_confidence < self.base_review_threshold:
            return 'NEW_TIGER'
        else:
            return 'REVIEW_REQUIRED'

class OpenSetDetector:
    def __init__(self, method: str = 'percentile', novelty_threshold: float = 0.65):
        self.method = method
        self.novelty_threshold = novelty_threshold

    def is_novel(self, top_similarities: list[float], identity_statistics: dict | None = None) -> tuple[bool, float, str]:
        if not top_similarities:
            return True, 1.0, "No candidates"
            
        top_1 = top_similarities[0]
        
        if self.method == 'percentile':
            if top_1 < self.novelty_threshold:
                return True, 1.0 - top_1, "Top similarity below novelty threshold"
            return False, top_1, "Match found"
            
        elif self.method == 'margin':
            if len(top_similarities) > 1:
                top_2 = top_similarities[1]
                margin = top_1 - top_2
                if margin < 0.05 and top_1 < 0.75:
                    return True, 1.0 - top_1, "Small margin and low top similarity"
            if top_1 < self.novelty_threshold:
                return True, 1.0 - top_1, "Top similarity below novelty threshold"
            return False, top_1, "Match found"
            
        elif self.method == 'distribution' and identity_statistics:
            if top_1 < self.novelty_threshold:
                return True, 1.0 - top_1, "Top similarity below novelty threshold"
            return False, top_1, "Match found"
            
        return False, top_1, "Match found"

    def update_statistics(self, tiger_id: str, new_similarity: float, statistics: dict) -> dict:
        stats = statistics.get(tiger_id, {"mean": 0.0, "std": 0.0, "count": 0})
        count = stats["count"]
        mean = stats["mean"]
        
        new_count = count + 1
        new_mean = mean + (new_similarity - mean) / new_count
        
        if count > 0:
            variance = (stats["std"] ** 2 * count + (new_similarity - mean) * (new_similarity - new_mean)) / new_count
            new_std = max(0.0, float(math.sqrt(variance)))
        else:
            new_std = 0.0
            
        statistics[tiger_id] = {"mean": new_mean, "std": new_std, "count": new_count}
        return statistics
