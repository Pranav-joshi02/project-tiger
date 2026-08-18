"""Multi-image identity memory for tiger Re-ID.

Manages identity prototypes per side (LEFT/RIGHT) using quality-weighted aggregation
of confirmed embeddings. Allows the system's memory to improve over time.
"""
import logging
from typing import Any
import numpy as np

logger = logging.getLogger(__name__)

def compute_prototype(embeddings: list[list[float]], quality_weights: list[float]) -> list[float]:
    """Compute a quality-weighted average prototype from multiple embeddings.
    
    Parameters
    ----------
    embeddings : list of 512-d feature vectors.
    quality_weights : list of 0-1 quality weights.
    
    Returns
    -------
    L2-normalized 512-d prototype vector.
    """
    if not embeddings:
        raise ValueError("Cannot compute prototype with empty embeddings list.")
        
    vectors = np.array(embeddings, dtype=np.float64)
    weights = np.array(quality_weights, dtype=np.float64)
    
    # Ensure some minimum weight so we don't divide by zero
    weights = np.clip(weights, 0.05, 1.0)
    
    # Weighted sum
    weighted_sum = np.sum(vectors * weights[:, np.newaxis], axis=0)
    
    # L2 normalize
    norm = np.linalg.norm(weighted_sum)
    if norm > 0:
        weighted_sum /= norm
        
    return weighted_sum.tolist()

def update_identity(tiger_id: str, side: str, session: Any) -> str | None:
    """Recompute and save the prototype for a specific tiger and side.
    
    This should be called after human confirmation or a very high-confidence auto-match.
    
    Returns
    -------
    embedding_id of the new/updated prototype, or None if failed.
    """
    from app.models.embedding import Embedding
    from app.models.tiger import Tiger
    
    # Fetch all confirmed embeddings for this tiger + side
    records = session.query(Embedding).filter(
        Embedding.tiger_id == tiger_id,
        Embedding.side == side,
        Embedding.confirmed == True,
        Embedding.is_prototype == False
    ).all()
    
    if not records:
        return None
        
    embeddings = [r.vector for r in records]
    weights = [r.quality_weight for r in records]
    
    prototype_vec = compute_prototype(embeddings, weights)
    
    # Find existing prototype or create new one
    prototype = session.query(Embedding).filter(
        Embedding.tiger_id == tiger_id,
        Embedding.side == side,
        Embedding.is_prototype == True
    ).first()
    
    if prototype:
        prototype.vector = prototype_vec
        prototype.quality_weight = 1.0
    else:
        prototype = Embedding(
            tiger_id=tiger_id,
            vector=prototype_vec,
            model_version=records[0].model_version,
            side=side,
            quality_weight=1.0,
            is_prototype=True,
            confirmed=True
        )
        session.add(prototype)
        session.flush() # get ID
        
    # Update Tiger record pointers
    tiger = session.query(Tiger).get(tiger_id)
    if tiger:
        if side == "LEFT":
            tiger.left_prototype_id = prototype.id
        elif side == "RIGHT":
            tiger.right_prototype_id = prototype.id
            
    return str(prototype.id)

def compute_multipart_prototype(embeddings_by_part: dict[str, list[list[float]]], quality_weights: list[float]) -> dict[str, list[float]]:
    """Compute prototypes for each body part separately."""
    prototypes = {}
    for part, embeddings in embeddings_by_part.items():
        try:
            prototypes[part] = compute_prototype(embeddings, quality_weights)
        except ValueError:
            pass
    return prototypes

def update_identity_multipart(tiger_id: str, side: str, session: Any) -> dict[str, str | None]:
    """Updates prototypes for global + head + flank + hind parts."""
    from app.models.embedding import Embedding
    from app.models.tiger import Tiger
    
    parts = ["global", "head", "flank", "hind"]
    updated_ids = {}
    
    for part in parts:
        records = session.query(Embedding).filter(
            Embedding.tiger_id == tiger_id,
            Embedding.side == side,
            Embedding.part_type == part,
            Embedding.confirmed == True,
            Embedding.is_prototype == False
        ).all()
        
        if not records:
            updated_ids[part] = None
            continue
            
        embeddings = [r.vector for r in records]
        weights = [r.quality_weight for r in records]
        
        prototype_vec = compute_prototype(embeddings, weights)
        
        prototype = session.query(Embedding).filter(
            Embedding.tiger_id == tiger_id,
            Embedding.side == side,
            Embedding.part_type == part,
            Embedding.is_prototype == True
        ).first()
        
        if prototype:
            prototype.vector = prototype_vec
            prototype.quality_weight = 1.0
        else:
            prototype = Embedding(
                tiger_id=tiger_id,
                vector=prototype_vec,
                model_version=records[0].model_version,
                side=side,
                part_type=part,
                quality_weight=1.0,
                is_prototype=True,
                confirmed=True
            )
            session.add(prototype)
            session.flush()
            
        updated_ids[part] = str(prototype.id)
        
    return updated_ids
