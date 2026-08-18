import numpy as np
from typing import List, Dict, Any

class ActiveLearningEngine:
    """
    Selects the most informative/uncertain samples from human review queues
    to prioritize labeling and retrain models. Uses margin, entropy, and diversity sampling.
    """
    def __init__(self, strategy: str = 'margin'):
        """
        Args:
            strategy (str): The sampling strategy to use ('margin', 'entropy', 'diversity').
        """
        self.strategy = strategy
        
    def _margin_sampling(self, probabilities: np.ndarray) -> np.ndarray:
        """Calculates margin (difference between top 2 class probabilities)."""
        if probabilities.shape[1] < 2:
            return np.zeros(probabilities.shape[0])
            
        sorted_probs = np.sort(probabilities, axis=1)
        margin = sorted_probs[:, -1] - sorted_probs[:, -2]
        # Lower margin means higher uncertainty
        return -margin 
        
    def _entropy_sampling(self, probabilities: np.ndarray) -> np.ndarray:
        """Calculates predictive entropy."""
        entropy = -np.sum(probabilities * np.log(probabilities + 1e-10), axis=1)
        return entropy
        
    def select_samples(self, samples: List[Dict[str, Any]], num_select: int = 10) -> List[Dict[str, Any]]:
        """
        Selects top informative samples for human review.
        
        Args:
            samples (List[Dict]): List of samples, each containing 'probabilities' or 'features'.
            num_select (int): Number of samples to select.
            
        Returns:
            List[Dict]: Subset of samples prioritized for review.
        """
        if not samples:
            return []
            
        num_select = min(num_select, len(samples))
        
        try:
            probs = np.array([s['probabilities'] for s in samples])
            
            if self.strategy == 'margin':
                scores = self._margin_sampling(probs)
            elif self.strategy == 'entropy':
                scores = self._entropy_sampling(probs)
            else:
                scores = np.random.rand(len(samples))
                
            top_indices = np.argsort(scores)[-num_select:][::-1]
            
            return [samples[i] for i in top_indices]
            
        except KeyError:
            return samples[:num_select]
