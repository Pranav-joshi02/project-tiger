"""Decision engine for tiger Re-ID matching with open-set calibration."""
from dataclasses import dataclass
from typing import Any, Union

@dataclass
class Decision:
    action: str  # AUTO_MATCH, NEW_TIGER, REVIEW_REQUIRED
    tiger_id: str | None
    reason: str
    metadata: dict[str, Any] | None = None

    @property
    def status(self) -> str:
        # Legacy support for unit tests
        if self.action == "AUTO_MATCH":
            return "AUTO_ASSIGN"
        return self.action

def decide(
    candidates_or_top: Union[list[dict[str, Any]], float],
    runner_up_or_auto: Union[float, None] = None,
    match_threshold: float = 0.85,
    review_threshold: float = 0.65,
    margin_threshold: float = 0.08,
) -> Decision:
    """Make open-set Re-ID decisions (MATCH, REVIEW, NEW).
    
    Supports legacy float inputs or the new candidate metadata dicts.
    """
    if isinstance(candidates_or_top, (int, float)):
        top_similarity = float(candidates_or_top)
        runner_up_similarity = float(runner_up_or_auto) if runner_up_or_auto is not None else 0.0
        margin = top_similarity - runner_up_similarity
        
        if top_similarity >= match_threshold and margin >= margin_threshold:
            return Decision("AUTO_MATCH", None, "threshold and candidate margin satisfied")
        if top_similarity < review_threshold:
            return Decision("NEW_TIGER", None, "no catalogue candidate has sufficient visual support")
        return Decision("REVIEW_REQUIRED", None, "identity evidence is ambiguous")
        
    candidates = candidates_or_top
    if not candidates:
        return Decision("NEW_TIGER", None, "No candidates found")
        
    top = candidates[0]
    top_sim = top["similarity"]
    
    if len(candidates) == 1:
        if top_sim >= match_threshold:
            return Decision("AUTO_MATCH", top["tiger_id"], f"Single match >= {match_threshold}", metadata={"top_sim": top_sim})
        if top_sim < review_threshold:
            return Decision("NEW_TIGER", None, f"Single match < {review_threshold}", metadata={"top_sim": top_sim})
        return Decision("REVIEW_REQUIRED", top["tiger_id"], f"Ambiguous single match", metadata={"top_sim": top_sim})
        
    runner_up = candidates[1]
    ru_sim = runner_up["similarity"]
    margin = top_sim - ru_sim
    
    meta = {"top_sim": top_sim, "ru_sim": ru_sim, "margin": margin}
    
    # Optional reranker support: if reranker applied final_score, use that for logic,
    # but still respect visual floor
    score_key = "final_score" if "final_score" in top else "similarity"
    top_score = top[score_key]
    ru_score = runner_up[score_key]
    score_margin = top_score - ru_score
    
    if top_score >= match_threshold and score_margin >= margin_threshold:
        return Decision("AUTO_MATCH", top["tiger_id"], "Match threshold and margin satisfied", meta)
        
    if top_score < review_threshold:
        return Decision("NEW_TIGER", None, "Insufficient match confidence", meta)
        
    return Decision("REVIEW_REQUIRED", top["tiger_id"], "Ambiguous identity match", meta)

def adaptive_decide(
    candidates: list[dict[str, Any]],
    quality: 'Any | None' = None,
    pose_compatibility: float = 1.0,
    match_threshold: float = 0.85,
    review_threshold: float = 0.65,
    margin_threshold: float = 0.08
) -> Decision:
    """Make decision using multi-factor confidence calibration and open-set detection."""
    from .confidence_model import ConfidenceCalibrator, OpenSetDetector, QualityVector

    if quality is None:
        return decide(candidates, None, match_threshold, review_threshold, margin_threshold)

    calibrator = ConfidenceCalibrator(
        base_match_threshold=match_threshold,
        base_review_threshold=review_threshold
    )
    detector = OpenSetDetector(method='percentile', novelty_threshold=review_threshold)
    
    if not candidates:
        return Decision("NEW_TIGER", None, "No candidates found")
        
    top = candidates[0]
    top_sim = top.get("final_score", top.get("similarity", 0.0))
    calibrated_conf = calibrator.calibrate(top_sim, quality, pose_compatibility)
    
    top_similarities = [c.get("final_score", c.get("similarity", 0.0)) for c in candidates]
    is_novel, novelty_conf, reason = detector.is_novel(top_similarities)
    
    if is_novel:
        meta = {"calibrated_confidence": calibrated_conf, "is_novel": is_novel, "novelty_confidence": novelty_conf}
        return Decision("NEW_TIGER", None, reason, meta)
        
    action = calibrator.classify(calibrated_conf)
    
    meta = {"calibrated_confidence": calibrated_conf, "is_novel": is_novel, "novelty_confidence": novelty_conf}
    if len(candidates) > 1:
        ru_sim = candidates[1].get("final_score", candidates[1].get("similarity", 0.0))
        ru_calibrated = calibrator.calibrate(ru_sim, quality, pose_compatibility)
        meta["margin"] = calibrated_conf - ru_calibrated
        if action == "AUTO_MATCH" and meta["margin"] < margin_threshold:
            action = "REVIEW_REQUIRED"
            reason = "Margin below threshold"
        else:
            reason = "Confidence model classification"
    else:
        reason = "Single candidate classification"
        
    return Decision(action, top.get("tiger_id"), reason, meta)
