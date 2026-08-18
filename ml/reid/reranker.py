"""Spatio-temporal reranking of Re-ID candidates.

Post-processes visual candidates by incorporating spatial and temporal context.
Candidates with biologically implausible movement speeds are penalised,
while candidates previously seen nearby are rewarded.

Crucially respects the "visual floor" rule: context can re-order ambiguous
matches but can NEVER override strong visual contradictions.
"""
import logging
from typing import Any
import uuid

logger = logging.getLogger(__name__)

VISUAL_FLOOR = 0.50

def rerank(
    candidates: list[dict[str, Any]], 
    query_station_id: str | uuid.UUID | None, 
    query_timestamp: Any, 
    session: Any
) -> list[dict[str, Any]]:
    """Rerank candidates using spatial and temporal heuristics."""
    if not candidates or not query_station_id or not query_timestamp:
        for c in candidates:
            c["spatial_score"] = 0.5
            c["temporal_score"] = 0.5
            c["final_score"] = c["similarity"]
        return [c for c in candidates if c["similarity"] >= VISUAL_FLOOR]
        
    from app.models.observation import Observation
    from app.models.station import Station
    
    # Pre-fetch query station coords
    q_station = session.query(Station).get(query_station_id)
    
    valid_candidates = []
    
    for c in candidates:
        if c["similarity"] < VISUAL_FLOOR:
            # Absolute rule: context cannot override strong visual mismatch
            continue
            
        tid = c["tiger_id"]
        
        # Simple heuristics for now (would use PostGIS in full implementation)
        # 1. Has tiger been seen at this exact station?
        obs_count_here = session.query(Observation).filter(
            Observation.tiger_id == tid,
            Observation.station_id == query_station_id
        ).count()
        
        spatial_score = 0.8 if obs_count_here > 0 else 0.5
        
        # 2. Temporal plausibility (stub)
        temporal_score = 0.5
        
        c["spatial_score"] = spatial_score
        c["temporal_score"] = temporal_score
        
        # Weighted combination: 80% visual, 10% spatial, 10% temporal
        c["final_score"] = (0.8 * c["similarity"]) + (0.1 * spatial_score) + (0.1 * temporal_score)
        
        valid_candidates.append(c)
        
    # Re-sort by final score
    valid_candidates.sort(key=lambda x: x["final_score"], reverse=True)
    return valid_candidates

def enhanced_rerank(
    candidates: list[dict[str, Any]], 
    query_parts: dict[str, list[float]] | None,
    query_quality: dict | None,
    query_station_id: str | uuid.UUID | None, 
    query_timestamp: Any, 
    session: Any
) -> list[dict[str, Any]]:
    """Rerank using multi-feature embeddings if available, then spatio-temporal."""
    if not candidates:
        return []

    # Step 1: Apply MultiFeatureReranker if query has multi-part embeddings
    if query_parts:
        from .multi_feature_reranker import MultiFeatureReranker
        reranker = MultiFeatureReranker()
        mf_results = reranker.rerank(query_parts, candidates, query_quality)
        
        # Merge back to candidates
        mf_dict = {r.tiger_id: r for r in mf_results}
        for c in candidates:
            if c["tiger_id"] in mf_dict:
                c["similarity"] = mf_dict[c["tiger_id"]].quality_adjusted_score
                c["multi_feature_score"] = mf_dict[c["tiger_id"]].quality_adjusted_score
                
        # Re-sort
        candidates.sort(key=lambda x: x["similarity"], reverse=True)
                
    # Step 2: Apply existing spatio-temporal reranking
    st_candidates = rerank(candidates, query_station_id, query_timestamp, session)
    
    # Step 3: Return Top-3 with multi-factor scores
    return st_candidates[:3]
