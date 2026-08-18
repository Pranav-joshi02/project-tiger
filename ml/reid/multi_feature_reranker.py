"""Multi-feature re-ranking for tiger Re-ID.

Second-stage re-ranker that combines global, flank/stripe, head, and hind
similarities with dynamic partial matching. Applied after pgvector retrieval
to produce more accurate final rankings.

Supports partial matching when query and candidate show different body parts,
and quality-aware scoring that adjusts confidence based on image quality.
"""
from dataclasses import dataclass
import math

@dataclass
class PartSimilarity:
    part_name: str
    query_available: bool
    candidate_available: bool
    similarity: float | None

@dataclass
class RerankerResult:
    tiger_id: str
    global_similarity: float
    part_similarities: list[PartSimilarity]
    weighted_score: float
    quality_adjusted_score: float
    matching_parts: int
    total_parts: int

class MultiFeatureReranker:
    def __init__(self, weights: dict[str, float] | None = None):
        if weights is None:
            self.weights = {"global": 0.30, "flank": 0.40, "head": 0.15, "hind": 0.15}
        else:
            self.weights = weights

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _compute_part_similarities(self, query_parts: dict[str, list[float]], candidate_parts: dict[str, list[float]]) -> list[PartSimilarity]:
        similarities = []
        all_parts = set(query_parts.keys()).union(candidate_parts.keys())
        for part in all_parts:
            q_avail = part in query_parts
            c_avail = part in candidate_parts
            sim = None
            if q_avail and c_avail:
                sim = self._cosine_similarity(query_parts[part], candidate_parts[part])
            similarities.append(PartSimilarity(
                part_name=part,
                query_available=q_avail,
                candidate_available=c_avail,
                similarity=sim
            ))
        return similarities

    def _dynamic_weight(self, available_parts: list[str]) -> dict[str, float]:
        total_weight = sum(self.weights.get(p, 0.0) for p in available_parts)
        if total_weight <= 0:
            return {p: 0.0 for p in available_parts}
        return {p: self.weights.get(p, 0.0) / total_weight for p in available_parts}

    def _quality_adjustment(self, score: float, quality_scores: dict | None) -> float:
        if not quality_scores:
            return score
        q = quality_scores.get("composite", 1.0) if isinstance(quality_scores, dict) else 1.0
        return score * (0.8 + 0.2 * q)

    def rerank(self, query_parts: dict[str, list[float]], candidates: list[dict], quality_scores: dict | None = None) -> list[RerankerResult]:
        results = []
        for candidate in candidates:
            c_parts = candidate.get("parts", {})
            part_sims = self._compute_part_similarities(query_parts, c_parts)
            
            available_parts = [ps.part_name for ps in part_sims if ps.similarity is not None]
            weights = self._dynamic_weight(available_parts)
            
            weighted_score = sum(ps.similarity * weights.get(ps.part_name, 0.0) for ps in part_sims if ps.similarity is not None)
            quality_adj = self._quality_adjustment(weighted_score, quality_scores)
            
            global_sim = 0.0
            for ps in part_sims:
                if ps.part_name == "global" and ps.similarity is not None:
                    global_sim = ps.similarity
                    break
                    
            results.append(RerankerResult(
                tiger_id=candidate.get("tiger_id", ""),
                global_similarity=global_sim,
                part_similarities=part_sims,
                weighted_score=weighted_score,
                quality_adjusted_score=quality_adj,
                matching_parts=len(available_parts),
                total_parts=len(part_sims)
            ))
            
        results.sort(key=lambda x: x.quality_adjusted_score, reverse=True)
        return results
