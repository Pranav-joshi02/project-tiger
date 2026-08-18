"""Multi-part embedding representation for tiger Re-ID.

Defines the data structure for multi-part body feature embeddings,
where each body region (head, torso/flank, hind) has its own
embedding vector, plus a global embedding and fused search vector.
"""
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any


logger = logging.getLogger(__name__)


@dataclass
class MultiPartEmbedding:
    """Represents a composite multi-part embedding for a tiger."""
    
    global_embedding: List[float]  # 512-D
    head_embedding: Optional[List[float]] = None  # 128-D
    flank_embedding: Optional[List[float]] = None  # 256-D
    hind_embedding: Optional[List[float]] = None  # 128-D
    fused_embedding: List[float] = field(default_factory=list)  # 512-D for pgvector search
    stripe_features: Optional[List[float]] = None  # 256-D Gabor stripe features
    visible_parts: List[str] = field(default_factory=list)  # e.g., ['head', 'torso', 'hind']
    pose_confidence: float = 0.0
    quality_scores: Optional[Dict[str, float]] = None
    model_version: str = 'multipart-v1'

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the multi-part embedding to a dictionary."""
        return asdict(self)

    def get_part_embedding(self, part: str) -> Optional[List[float]]:
        """Retrieves the embedding for a specific part by name."""
        part_map = {
            'head': self.head_embedding,
            'torso': self.flank_embedding,
            'flank': self.flank_embedding,
            'hind': self.hind_embedding,
            'global': self.global_embedding,
            'fused': self.fused_embedding,
            'stripes': self.stripe_features
        }
        return part_map.get(part.lower())

    def get_visible_part_embeddings(self) -> Dict[str, List[float]]:
        """Returns a dictionary of part name to embedding only for visible parts."""
        result = {}
        for part in self.visible_parts:
            emb = self.get_part_embedding(part)
            if emb is not None:
                result[part] = emb
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MultiPartEmbedding':
        """Deserializes a dictionary into a MultiPartEmbedding."""
        # Filter out keys that aren't in the dataclass fields to avoid errors
        # if the schema changes over time.
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)

    @classmethod
    def from_legacy(cls, embedding: List[float]) -> 'MultiPartEmbedding':
        """Creates a multi-part embedding from an old single 512-D embedding format."""
        logger.info("Converting legacy 512-D embedding to MultiPartEmbedding format.")
        return cls(
            global_embedding=embedding,
            fused_embedding=embedding,  # Use global as fused for legacy
            visible_parts=['global'],
            pose_confidence=0.0,
            model_version='legacy-v0'
        )
