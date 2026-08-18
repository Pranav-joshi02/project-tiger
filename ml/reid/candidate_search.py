"""Candidate search using cosine similarity with rich metadata and strict negative constraint filtering."""
from typing import Any, Optional, Set
import uuid
import logging
import numpy as np
from sqlalchemy.orm import Session
from app.models.embedding import Embedding
from app.models.tiger import Tiger
from app.models.flank import FlankSide

logger = logging.getLogger(__name__)


def get_negative_constraints(
    session: Session,
    image_id: Optional[uuid.UUID | str] = None,
    image_sha256: Optional[str] = None,
    flank_id: Optional[uuid.UUID | str] = None,
    detection_id: Optional[uuid.UUID | str] = None,
    exclude_tiger_ids: Optional[Set[str] | list[str]] = None,
) -> Set[str]:
    """Retrieve set of rejected tiger IDs that must strictly NOT match this query."""
    blocked: Set[str] = set()
    if exclude_tiger_ids:
        for tid in exclude_tiger_ids:
            blocked.add(str(tid))

    try:
        from app.models.negative_constraint import NegativeConstraint
        query = session.query(NegativeConstraint)
        conditions = []

        if image_id:
            try:
                img_uuid = uuid.UUID(str(image_id))
                conditions.append(NegativeConstraint.image_id == img_uuid)
            except ValueError:
                pass

        if flank_id:
            try:
                flk_uuid = uuid.UUID(str(flank_id))
                conditions.append(NegativeConstraint.flank_id == flk_uuid)
            except ValueError:
                pass

        if detection_id:
            try:
                det_uuid = uuid.UUID(str(detection_id))
                conditions.append(NegativeConstraint.detection_id == det_uuid)
            except ValueError:
                pass

        if image_sha256:
            conditions.append(NegativeConstraint.image_sha256 == str(image_sha256))

        if conditions:
            from sqlalchemy import or_
            constraints = query.filter(or_(*conditions)).all()
            for c in constraints:
                blocked.add(str(c.tiger_id))
    except Exception as e:
        logger.debug(f"Negative constraints lookup note: {e}")

    return blocked


def search_candidates(
    query_vector: list[float], 
    session: Session, 
    side_filter: str | None = None,
    k: int = 20,
    image_id: Optional[uuid.UUID | str] = None,
    image_sha256: Optional[str] = None,
    flank_id: Optional[uuid.UUID | str] = None,
    detection_id: Optional[uuid.UUID | str] = None,
    exclude_tiger_ids: Optional[Set[str] | list[str]] = None,
) -> list[dict[str, Any]]:
    """Search for matching tiger individuals using cosine distance with strict negative constraint enforcement.
    
    Includes rich metadata (side, quality, observations) for reranking.
    Filters out incompatible flank sides if side_filter is provided.
    Strictly disqualifies tigers that were previously rejected for this query.
    """
    if not query_vector:
        return []

    # Get strict rejected claim blocklist
    blocked_tiger_ids = get_negative_constraints(
        session=session,
        image_id=image_id,
        image_sha256=image_sha256,
        flank_id=flank_id,
        detection_id=detection_id,
        exclude_tiger_ids=exclude_tiger_ids,
    )

    q_vec = np.array(query_vector, dtype=np.float32)
    norm_q = np.linalg.norm(q_vec)
    if norm_q > 0:
        q_vec = q_vec / norm_q

    query = session.query(Embedding, Tiger).join(Tiger, Embedding.tiger_id == Tiger.id)
    
    # Optionally filter by compatible sides
    if side_filter and side_filter in [FlankSide.LEFT, FlankSide.RIGHT]:
        query = query.filter(
            (Embedding.side == side_filter) | (Embedding.side.is_(None)) | (Embedding.side == FlankSide.UNKNOWN)
        )

    results = query.filter(Embedding.tiger_id.is_not(None)).all()

    candidates_raw = []
    for emb, tiger in results:
        t_id_str = str(tiger.id)
        t_code_str = str(tiger.code)

        # STRICT NEGATIVE CONSTRAINT: Skip any rejected claim
        if t_id_str in blocked_tiger_ids or t_code_str in blocked_tiger_ids:
            logger.info(f"Strictly blocking rejected claim match: Tiger {tiger.code} ({t_id_str})")
            continue

        emb_vec = emb.vector
        if emb_vec is not None:
            try:
                if isinstance(emb_vec, str):
                    emb_vec = [float(x) for x in emb_vec.strip("[]").split(",") if x.strip()]
                e_arr = np.asarray(emb_vec, dtype=np.float32)
                norm_e = np.linalg.norm(e_arr)
                if norm_e > 0:
                    e_arr = e_arr / norm_e
                similarity = float(np.dot(q_vec, e_arr))
            except Exception:
                similarity = 0.0
        else:
            similarity = 0.0

        similarity = max(0.0, min(1.0, similarity))

        candidates_raw.append({
            "tiger_id": t_id_str,
            "tiger_code": tiger.code,
            "name": tiger.name,
            "similarity": similarity,
            "embedding_id": str(emb.id),
            "side": getattr(emb, "side", None),
            "quality_weight": getattr(emb, "quality_weight", 1.0),
            "is_prototype": getattr(emb, "is_prototype", False),
            "observation_count": tiger.total_observations,
            "last_seen": tiger.last_seen.isoformat() if tiger.last_seen else None,
        })

    # Sort descending by similarity
    candidates_raw.sort(key=lambda x: x["similarity"], reverse=True)

    # Deduplicate by tiger_id keeping highest similarity
    candidates = []
    seen_tigers = set()
    for c in candidates_raw:
        if c["tiger_id"] not in seen_tigers:
            seen_tigers.add(c["tiger_id"])
            candidates.append(c)
            if len(candidates) >= k:
                break

    return candidates
