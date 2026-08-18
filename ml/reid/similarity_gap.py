"""Similarity Gap Criterion and Decision Ambiguity Evaluator.

Implements the similarity gap decision model:
G = S_1 - S_2
where S_1 is the highest candidate similarity and S_2 is the second highest similarity.

Rules:
- High similarity (S_1 >= auto_threshold) + Large gap (G >= margin_threshold) -> AUTO_MATCH (High confidence)
- High similarity (S_1 >= auto_threshold) + Small gap (G < margin_threshold) -> REVIEW_REQUIRED (Ambiguous twin match)
- Moderate similarity (review_threshold <= S_1 < auto_threshold) -> REVIEW_REQUIRED
- Low similarity (S_1 < review_threshold) -> NEW_TIGER (Novel open-set candidate)
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class SimilarityGapResult:
    top1_tiger_id: Optional[str]
    top1_similarity: float
    top2_tiger_id: Optional[str]
    top2_similarity: float
    gap: float
    decision_action: str  # AUTO_MATCH, REVIEW_REQUIRED, NEW_TIGER
    confidence_score: float
    reason: str


class SimilarityGapEvaluator:
    """
    Evaluates top-K retrieval candidates using both absolute similarity
    and relative margin gap to prevent false auto-matches on lookalike tigers.
    """
    def __init__(
        self,
        auto_threshold: float = 0.85,
        review_threshold: float = 0.65,
        margin_threshold: float = 0.08,
    ):
        self.auto_threshold = auto_threshold
        self.review_threshold = review_threshold
        self.margin_threshold = margin_threshold

    def evaluate(self, ranked_candidates: List[Dict[str, Any]]) -> SimilarityGapResult:
        """
        Evaluates ranked candidates and produces an ambiguity-aware decision.
        """
        if not ranked_candidates:
            return SimilarityGapResult(
                top1_tiger_id=None,
                top1_similarity=0.0,
                top2_tiger_id=None,
                top2_similarity=0.0,
                gap=0.0,
                decision_action="NEW_TIGER",
                confidence_score=0.0,
                reason="No candidate matches found in database.",
            )

        top1 = ranked_candidates[0]
        s1 = float(top1.get("similarity", top1.get("score", 0.0)))
        t1_id = top1.get("tiger_id", top1.get("id"))

        if len(ranked_candidates) > 1:
            top2 = ranked_candidates[1]
            s2 = float(top2.get("similarity", top2.get("score", 0.0)))
            t2_id = top2.get("tiger_id", top2.get("id"))
        else:
            s2 = 0.0
            t2_id = None

        gap = max(0.0, s1 - s2)

        # Decision Logic
        if s1 >= self.auto_threshold:
            if gap >= self.margin_threshold:
                action = "AUTO_MATCH"
                reason = f"High similarity ({s1:.3f}) with decisive margin gap ({gap:.3f} >= {self.margin_threshold})."
                conf = min(0.99, s1 + gap * 0.1)
            else:
                action = "REVIEW_REQUIRED"
                reason = f"High similarity ({s1:.3f}) but ambiguous margin gap ({gap:.3f} < {self.margin_threshold}) with {t2_id} ({s2:.3f})."
                conf = s1 * 0.90
        elif s1 >= self.review_threshold:
            action = "REVIEW_REQUIRED"
            reason = f"Moderate similarity ({s1:.3f}) within human verification band."
            conf = s1
        else:
            action = "NEW_TIGER"
            reason = f"Low top similarity ({s1:.3f} < {self.review_threshold}); novel tiger individual."
            conf = 1.0 - s1

        return SimilarityGapResult(
            top1_tiger_id=t1_id,
            top1_similarity=s1,
            top2_tiger_id=t2_id,
            top2_similarity=s2,
            gap=gap,
            decision_action=action,
            confidence_score=conf,
            reason=reason,
        )
