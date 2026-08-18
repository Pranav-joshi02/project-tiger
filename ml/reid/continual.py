import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict

class ContinualReID:
    """
    Incremental gallery updates as new tigers are confirmed by human reviewers
    without catastrophic forgetting. Manages an exemplar replay memory buffer
    and dynamic prototype adaptation.
    """
    def __init__(self, memory_size_per_class: int = 10, feature_dim: int = 512):
        """
        Args:
            memory_size_per_class (int): Number of exemplars to keep per identity.
            feature_dim (int): Dimensionality of the feature embeddings.
        """
        self.memory_size_per_class = memory_size_per_class
        self.feature_dim = feature_dim
        self.exemplar_memory: Dict[str, List[np.ndarray]] = defaultdict(list)
        self.prototypes: Dict[str, np.ndarray] = {}
        
    def _update_prototype(self, tiger_id: str):
        """Recomputes the prototype for a given identity."""
        if not self.exemplar_memory[tiger_id]:
            return
            
        features = np.stack(self.exemplar_memory[tiger_id])
        prototype = np.mean(features, axis=0)
        
        # Normalize prototype
        norm = np.linalg.norm(prototype)
        if norm > 0:
            prototype = prototype / norm
            
        self.prototypes[tiger_id] = prototype
        
    def add_exemplar(self, tiger_id: str, feature: List[float]):
        """
        Adds a new confirmed exemplar to the memory buffer and updates prototypes.
        
        Args:
            tiger_id (str): The confirmed identity.
            feature (List[float]): The feature embedding.
        """
        feat_arr = np.array(feature, dtype=np.float32)
        
        if len(self.exemplar_memory[tiger_id]) >= self.memory_size_per_class:
            evict_idx = np.random.randint(0, self.memory_size_per_class)
            self.exemplar_memory[tiger_id].pop(evict_idx)
            
        self.exemplar_memory[tiger_id].append(feat_arr)
        self._update_prototype(tiger_id)
        
    def get_gallery(self) -> Dict[str, List[float]]:
        """
        Returns the current prototypes as a gallery for matching.
        
        Returns:
            Dict[str, List[float]]: Mapping of tiger ID to prototype embedding.
        """
        return {tid: proto.tolist() for tid, proto in self.prototypes.items()}
