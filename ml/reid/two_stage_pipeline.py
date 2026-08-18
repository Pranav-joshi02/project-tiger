"""Two-stage tiger identification pipeline.

Stage A: Fast Candidate Retrieval
- Query embedding (512-D) -> pgvector / HNSW vector index -> Top-20 candidates

Stage B: Fine-Grained Accurate Verification
- Multi-biometric feature comparison
- Stripe geometry & topological alignment
- Quality-aware score weighting
- Similarity gap margin checking (G = S_1 - S_2)
- Open-set novel individual decision
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np

from ml.reid.multi_feature_reranker import MultiFeatureReranker
from ml.reid.stripe_geometry import StripeGeometryDescriptor
from ml.reid.similarity_gap import SimilarityGapEvaluator, SimilarityGapResult
from ml.reid.calibration import CalibratedConfidence


@dataclass
class IdentificationOutput:
    query_id: str
    decision: str  # AUTO_MATCH, REVIEW_REQUIRED, NEW_TIGER
    matched_tiger_id: Optional[str]
    calibrated_confidence: float
    similarity_gap: float
    ranked_candidates: List[Dict[str, Any]]
    evidence_summary: str


class TwoStageIdentifier:
    """
    Two-stage identification engine combining fast vector search with
    fine-grained multi-factor verification.
    """
    def __init__(
        self,
        top_k_stage_a: int = 20,
        final_k_stage_b: int = 3,
        auto_threshold: float = 0.85,
        review_threshold: float = 0.65,
        margin_threshold: float = 0.08,
    ):
        self.top_k_stage_a = top_k_stage_a
        self.final_k_stage_b = final_k_stage_b
        self.reranker = MultiFeatureReranker()
        self.stripe_geom = StripeGeometryDescriptor()
        self.gap_evaluator = SimilarityGapEvaluator(
            auto_threshold=auto_threshold,
            review_threshold=review_threshold,
            margin_threshold=margin_threshold,
        )
        self.calibrator = CalibratedConfidence()

    def identify(
        self,
        query_parts: Dict[str, List[float]],
        stage_a_candidates: List[Dict[str, Any]],
        query_quality: Optional[Dict[str, float]] = None,
        query_id: str = "query",
        exclude_tiger_ids: Optional[set | list] = None,
    ) -> IdentificationOutput:
        """
        Executes Stage B verification on Top-K candidates retrieved from Stage A.
        Strictly filters out any excluded / rejected tiger claims.
        """
        blocked_ids = {str(tid) for tid in exclude_tiger_ids} if exclude_tiger_ids else set()

        filtered_candidates = [
            c for c in stage_a_candidates 
            if str(c.get("tiger_id", c.get("id", ""))) not in blocked_ids
            and str(c.get("tiger_code", "")) not in blocked_ids
        ]

        if not filtered_candidates:
            return IdentificationOutput(
                query_id=query_id,
                decision="NEW_TIGER",
                matched_tiger_id=None,
                calibrated_confidence=0.0,
                similarity_gap=0.0,
                ranked_candidates=[],
                evidence_summary="No eligible candidates retrieved (prior rejected claims strictly excluded).",
            )

        # 1. Multi-feature & stripe re-ranking (Stage B)
        formatted_cands_for_reranker = []
        for cand in filtered_candidates:
            if "parts" in cand:
                formatted_cands_for_reranker.append(cand)
            else:
                parts = {k: v for k, v in cand.items() if k in ("global", "flank", "head", "hind", "tail") and isinstance(v, list)}
                formatted_cands_for_reranker.append({
                    "tiger_id": cand.get("tiger_id", cand.get("id", "UNKNOWN")),
                    "parts": parts,
                })

        rerank_results = self.reranker.rerank(
            query_parts=query_parts,
            candidates=formatted_cands_for_reranker,
            quality_scores=query_quality,
        )


        formatted_candidates = []
        for r in rerank_results:
            formatted_candidates.append({
                "tiger_id": r.tiger_id,
                "similarity": r.quality_adjusted_score,
                "global_similarity": r.global_similarity,
                "weighted_score": r.weighted_score,
                "matching_parts": r.matching_parts,
            })

        # 2. Similarity gap & margin ambiguity evaluation
        gap_res = self.gap_evaluator.evaluate(formatted_candidates)

        # 3. Probability calibration
        calibrated_prob = self.calibrator.calibrate(
            similarity=gap_res.top1_similarity,
            quality_vector=query_quality,
            method="platt",
        )

        return IdentificationOutput(
            query_id=query_id,
            decision=gap_res.decision_action,
            matched_tiger_id=gap_res.top1_tiger_id,
            calibrated_confidence=calibrated_prob,
            similarity_gap=gap_res.gap,
            ranked_candidates=formatted_candidates[:self.final_k_stage_b],
            evidence_summary=gap_res.reason,
        )
