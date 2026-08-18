"""Multi-embedding identity gallery for tiger Re-ID.

Stores and manages multiple embeddings per individual tiger, organized by
flank side and body part. Supports gallery-based matching where a query is
compared against all stored observations, not just a single prototype.

Architecture per tiger:
    Tiger T001
    ├── Left-flank embeddings (observation 001, 018, 047)
    ├── Right-flank embeddings (observation 004, 021)
    ├── Head embeddings
    ├── Full-body embeddings
    └── Stripe descriptors
"""

import uuid
import numpy as np
from dataclasses import dataclass

@dataclass
class GalleryEntry:
    embedding_id: str
    embedding: list[float]
    side: str
    part_type: str
    quality_weight: float
    observation_id: str | None
    timestamp: str | None
    is_prototype: bool = False

class IdentityGallery:
    def __init__(self):
        self._storage: dict[str, list[GalleryEntry]] = {}

    def add_observation(
        self, 
        tiger_id: str, 
        embedding: list[float], 
        side: str = 'UNKNOWN', 
        part_type: str = 'global', 
        quality_weight: float = 1.0, 
        observation_id: str | None = None, 
        timestamp: str | None = None
    ) -> GalleryEntry:
        if tiger_id not in self._storage:
            self._storage[tiger_id] = []
            
        entry = GalleryEntry(
            embedding_id=uuid.uuid4().hex,
            embedding=embedding,
            side=side,
            part_type=part_type,
            quality_weight=quality_weight,
            observation_id=observation_id,
            timestamp=timestamp,
            is_prototype=False
        )
        self._storage[tiger_id].append(entry)
        return entry

    def get_gallery(self, tiger_id: str, side: str | None = None, part_type: str | None = None) -> list[GalleryEntry]:
        if tiger_id not in self._storage:
            return []
            
        results = self._storage[tiger_id]
        if side is not None:
            results = [e for e in results if e.side == side]
        if part_type is not None:
            results = [e for e in results if e.part_type == part_type]
            
        return results

    def compute_prototype(self, tiger_id: str, side: str = 'LEFT', part_type: str = 'global') -> list[float]:
        entries = self.get_gallery(tiger_id, side, part_type)
        if not entries:
            return []
            
        vectors = np.array([e.embedding for e in entries], dtype=np.float64)
        weights = np.array([e.quality_weight for e in entries], dtype=np.float64)
        weights = np.clip(weights, 0.05, 1.0)
        
        weighted_sum = np.sum(vectors * weights[:, np.newaxis], axis=0)
        norm = np.linalg.norm(weighted_sum)
        if norm > 0:
            weighted_sum /= norm
            
        return weighted_sum.tolist()

    def match_against_gallery(self, query_embedding: list[float], tiger_id: str, side: str | None = None, part_type: str = 'global') -> dict:
        entries = self.get_gallery(tiger_id, side, part_type)
        if not entries:
            return {
                'max_similarity': 0.0,
                'mean_similarity': 0.0,
                'median_similarity': 0.0,
                'num_comparisons': 0,
                'best_match_entry': None
            }
            
        query_vec = np.array(query_embedding, dtype=np.float64)
        gallery_vecs = np.array([e.embedding for e in entries], dtype=np.float64)
        
        # Cosine similarity assuming L2 normalized
        similarities = np.dot(gallery_vecs, query_vec)
        
        max_idx = np.argmax(similarities)
        
        return {
            'max_similarity': float(np.max(similarities)),
            'mean_similarity': float(np.mean(similarities)),
            'median_similarity': float(np.median(similarities)),
            'num_comparisons': len(entries),
            'best_match_entry': entries[max_idx]
        }

    def match_all_tigers(self, query_embedding: list[float], side: str | None = None, part_type: str = 'global', top_k: int = 5) -> list[dict]:
        results = []
        for tiger_id in self._storage.keys():
            match_result = self.match_against_gallery(query_embedding, tiger_id, side, part_type)
            if match_result['num_comparisons'] > 0:
                match_result['tiger_id'] = tiger_id
                results.append(match_result)
                
        results.sort(key=lambda x: x['max_similarity'], reverse=True)
        return results[:top_k]

    def remove_observation(self, tiger_id: str, embedding_id: str) -> bool:
        if tiger_id not in self._storage:
            return False
            
        initial_len = len(self._storage[tiger_id])
        self._storage[tiger_id] = [e for e in self._storage[tiger_id] if e.embedding_id != embedding_id]
        
        return len(self._storage[tiger_id]) < initial_len

    def get_statistics(self, tiger_id: str) -> dict:
        if tiger_id not in self._storage:
            return {}
            
        stats = {}
        for entry in self._storage[tiger_id]:
            key = f"{entry.side}_{entry.part_type}"
            stats[key] = stats.get(key, 0) + 1
            
        return stats
