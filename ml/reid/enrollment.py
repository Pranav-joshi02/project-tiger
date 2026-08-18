"""Tiger identity enrollment module."""
import logging
from typing import Any
import uuid

logger = logging.getLogger(__name__)

def enroll(
    tiger_id: str | None,
    embedding_id: str,
    session: Any,
    is_confirmed: bool = False
) -> str:
    """Enroll an embedding into a tiger identity.
    
    If tiger_id is None, a new Tiger identity is created.
    """
    from app.models.tiger import Tiger, TigerStatus
    from app.models.embedding import Embedding
    
    emb = session.query(Embedding).get(uuid.UUID(embedding_id))
    if not emb:
        raise ValueError(f"Embedding {embedding_id} not found")
        
    if not tiger_id:
        # Create new tiger
        tiger = Tiger(
            code=f"T-{uuid.uuid4().hex[:6].upper()}",
            status=TigerStatus.PROVISIONAL if not is_confirmed else TigerStatus.CONFIRMED
        )
        session.add(tiger)
        session.flush()
        tiger_id_obj = tiger.id
    else:
        tiger_id_obj = uuid.UUID(tiger_id)
        tiger = session.query(Tiger).get(tiger_id_obj)
        if not tiger:
            raise ValueError(f"Tiger {tiger_id} not found")
            
    # Assign embedding to tiger
    emb.tiger_id = tiger_id_obj
    emb.confirmed = is_confirmed
    
    # If confirmed, optionally recompute prototype
    if is_confirmed and emb.side:
        try:
            from ml.reid.identity_memory import update_identity
            update_identity(str(tiger_id_obj), emb.side, session)
        except Exception as e:
            logger.warning(f"Failed to update prototype during enrollment: {e}")
            
    return str(tiger_id_obj)
