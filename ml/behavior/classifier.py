import numpy as np
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple
from ml.tracking.tracker import Tracklet

class BehaviorClass(Enum):
    """Enumeration of recognizable tiger behaviors."""
    WALKING = "WALKING"
    RUNNING = "RUNNING"
    RESTING = "RESTING"
    FEEDING = "FEEDING"
    DRINKING = "DRINKING"
    TERRITORIAL_MARKING = "TERRITORIAL_MARKING"
    TRAIL_CROSSING = "TRAIL_CROSSING"
    HUNTING = "HUNTING"
    AGGRESSIVE_INTERACTION = "AGGRESSIVE_INTERACTION"
    MATERNAL_CARE = "MATERNAL_CARE"
    UNKNOWN = "UNKNOWN"

@dataclass
class BehaviorPrediction:
    """Dataclass holding behavior classification results."""
    behavior: BehaviorClass
    confidence: float
    trajectory_velocity: float
    sequence_length: int
    details: Dict[str, Any] = field(default_factory=dict)

class TigerBehaviorClassifier:
    """
    Classifies behavior from temporal motion vectors, posture aspect ratios,
    and spatial displacement.
    """
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initializes the behavior classifier.
        
        Args:
            config (Dict): Configuration parameters.
        """
        self.config = config or {}
        
    def _compute_velocity(self, bboxes: List[Tuple[float, float, float, float]], fps: float) -> float:
        """Computes average velocity from bounding box centers."""
        if len(bboxes) < 2:
            return 0.0
            
        centers = []
        for x1, y1, x2, y2 in bboxes:
            centers.append(((x1 + x2) / 2, (y1 + y2) / 2))
            
        displacements = []
        for i in range(1, len(centers)):
            dx = centers[i][0] - centers[i-1][0]
            dy = centers[i][1] - centers[i-1][1]
            displacements.append(np.sqrt(dx**2 + dy**2))
            
        avg_displacement = np.mean(displacements)
        return float(avg_displacement * fps)
        
    def classify_sequence(self, tracklet: Tracklet, fps: float = 10.0) -> BehaviorPrediction:
        """
        Classifies the behavior of a tiger over a tracklet sequence.
        
        Args:
            tracklet (Tracklet): The tracked sequence of the tiger.
            fps (float): Frames per second of the sequence.
            
        Returns:
            BehaviorPrediction: The predicted behavior and associated metrics.
        """
        seq_len = len(tracklet.bboxes)
        if seq_len == 0:
            return BehaviorPrediction(
                behavior=BehaviorClass.UNKNOWN,
                confidence=0.0,
                trajectory_velocity=0.0,
                sequence_length=0,
                details={"reason": "empty tracklet"}
            )
            
        velocity = self._compute_velocity(tracklet.bboxes, fps)
        
        # Simple heuristic classification for demonstration
        behavior = BehaviorClass.UNKNOWN
        confidence = 0.5
        
        if velocity > 50.0:
            behavior = BehaviorClass.RUNNING
            confidence = 0.85
        elif velocity > 5.0:
            behavior = BehaviorClass.WALKING
            confidence = 0.90
        else:
            behavior = BehaviorClass.RESTING
            confidence = 0.75
            
        aspect_ratios = []
        for b in tracklet.bboxes:
            width = b[2] - b[0]
            height = b[3] - b[1]
            aspect_ratios.append(abs(width / (height + 1e-6)))
            
        return BehaviorPrediction(
            behavior=behavior,
            confidence=confidence,
            trajectory_velocity=velocity,
            sequence_length=seq_len,
            details={"aspect_ratios": aspect_ratios}
        )
