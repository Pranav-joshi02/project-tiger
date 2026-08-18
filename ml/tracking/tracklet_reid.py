import numpy as np
from typing import List, Dict, Optional, Tuple
from ml.tracking.tracker import Tracklet

class TrackletReID:
    """
    Sequence-level Re-ID aggregating features across a tracklet.
    Matches tracklet embeddings against identity gallery.
    """
    def __init__(self, gallery: Optional[Dict[str, List[float]]] = None):
        """
        Initializes the Tracklet ReID model.
        
        Args:
            gallery (Dict[str, List[float]]): Identity gallery mapping tiger ID to embedding.
        """
        self.gallery = gallery or {}
        
    def aggregate_tracklet_features(self, tracklet: Tracklet) -> List[float]:
        """
        Aggregates features across a tracklet using quality-weighted temporal attention pooling.
        
        Args:
            tracklet (Tracklet): The tracklet containing frame-level features and confidences.
            
        Returns:
            List[float]: Aggregated sequence-level embedding.
        """
        if not tracklet.features or not tracklet.confidences:
            return []
            
        features = np.array(tracklet.features)
        confidences = np.array(tracklet.confidences)
        
        # Normalize confidences for weighting
        weights = confidences / (np.sum(confidences) + 1e-6)
        weights = weights.reshape(-1, 1)
        
        # Weighted temporal pooling
        aggregated = np.sum(features * weights, axis=0)
        
        # L2 normalization
        norm = np.linalg.norm(aggregated)
        if norm > 0:
            aggregated = aggregated / norm
            
        return aggregated.tolist()
        
    def match(self, tracklet: Tracklet, top_k: int = 1) -> List[Tuple[str, float]]:
        """
        Matches tracklet embedding against the identity gallery.
        
        Args:
            tracklet (Tracklet): The tracklet to identify.
            top_k (int): Number of top matches to return.
            
        Returns:
            List[Tuple[str, float]]: Top matches with (tiger_id, similarity_score).
        """
        query_emb = np.array(self.aggregate_tracklet_features(tracklet))
        if query_emb.size == 0 or not self.gallery:
            return [("unknown", 0.0)]
            
        results = []
        for tiger_id, gallery_emb in self.gallery.items():
            g_emb = np.array(gallery_emb)
            sim = np.dot(query_emb, g_emb)  # Cosine similarity assuming normalized vectors
            results.append((tiger_id, float(sim)))
            
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
