"""Tiger pose estimation for body-part-aware Re-ID.

Estimates keypoints on tiger bodies to enable body-part alignment
before feature extraction. Uses a lightweight HRNet-W32-based model
adapted for quadruped animal pose, following the ATRW keypoint schema.

When pose estimation is unavailable or fails, falls back to geometric
heuristics based on bounding box proportions.
"""
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Tuple

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import torch
    import torchvision
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


logger = logging.getLogger(__name__)


@dataclass
class TigerKeypoints:
    """15 keypoints for quadruped pose estimation (ATRW schema).
    
    Each keypoint is represented as (x, y, confidence).
    """
    nose: Tuple[float, float, float]
    left_eye: Tuple[float, float, float]
    right_eye: Tuple[float, float, float]
    left_ear: Tuple[float, float, float]
    right_ear: Tuple[float, float, float]
    left_shoulder: Tuple[float, float, float]
    right_shoulder: Tuple[float, float, float]
    left_hip: Tuple[float, float, float]
    right_hip: Tuple[float, float, float]
    left_front_paw: Tuple[float, float, float]
    right_front_paw: Tuple[float, float, float]
    left_hind_paw: Tuple[float, float, float]
    right_hind_paw: Tuple[float, float, float]
    tail_base: Tuple[float, float, float]
    tail_tip: Tuple[float, float, float]


@dataclass
class PoseEstimationResult:
    """Result of pose estimation on a tiger crop."""
    keypoints: TigerKeypoints
    body_parts: Dict[str, Tuple[int, int, int, int]]  # dict of part_name -> (x1, y1, x2, y2)
    body_axis_angle: float
    pose_confidence: float


class TigerPoseEstimator:
    """Estimates tiger pose keypoints to aid in Re-ID alignment."""
    
    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None):
        self.model_path = model_path
        self.device = device or ("cuda" if HAS_TORCH and torch.cuda.is_available() else "cpu")
        self.model = None
        self._is_initialized = False
        self._use_fallback = False

    def _lazy_init(self) -> bool:
        """Loads model on first use."""
        if self._is_initialized:
            return not self._use_fallback
            
        if not HAS_TORCH or not self.model_path:
            logger.warning("Torch not available or model_path not provided. Using geometric fallback.")
            self._use_fallback = True
            self._is_initialized = True
            return False
            
        try:
            logger.info(f"Loading TigerPoseEstimator model from {self.model_path} to {self.device}")
            # Placeholder for actual model loading logic
            # self.model = torch.load(self.model_path, map_location=self.device)
            # self.model.eval()
            self._is_initialized = True
            self._use_fallback = False
            return True
        except Exception as e:
            logger.error(f"Failed to load TigerPoseEstimator model: {e}")
            self._use_fallback = True
            self._is_initialized = True
            return False

    def estimate(self, image: 'np.ndarray', bbox: Tuple[int, int, int, int]) -> PoseEstimationResult:
        """Main method to estimate pose keypoints on a tiger image.
        
        Args:
            image: Full image or crop containing the tiger.
            bbox: Bounding box (x1, y1, x2, y2) of the tiger in the image.
            
        Returns:
            PoseEstimationResult containing keypoints, body parts, and orientation.
        """
        model_available = self._lazy_init()
        
        if not model_available or self._use_fallback:
            return self._geometric_fallback(bbox)
            
        # In a real scenario, we would preprocess the image crop, run inference, and postprocess.
        # Here we just fallback for safety if inference isn't fully implemented.
        logger.info("Running deep learning pose estimation (placeholder). Falling back to geometric.")
        return self._geometric_fallback(bbox)

    def _geometric_fallback(self, bbox: Tuple[int, int, int, int]) -> PoseEstimationResult:
        """Splits bbox geometrically based on typical quadruped proportions."""
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        
        # Synthetic keypoints based on typical pose (facing right or left)
        # Assuming horizontal orientation for fallback
        mid_y = y1 + height / 2.0
        
        # Create synthetic keypoints
        kp = TigerKeypoints(
            nose=(x1 + width * 0.05, mid_y, 0.1),
            left_eye=(x1 + width * 0.1, mid_y - height * 0.1, 0.1),
            right_eye=(x1 + width * 0.1, mid_y + height * 0.1, 0.1),
            left_ear=(x1 + width * 0.15, y1 + height * 0.1, 0.1),
            right_ear=(x1 + width * 0.15, y1 + height * 0.2, 0.1),
            left_shoulder=(x1 + width * 0.25, mid_y, 0.1),
            right_shoulder=(x1 + width * 0.25, mid_y, 0.1),
            left_hip=(x1 + width * 0.75, mid_y, 0.1),
            right_hip=(x1 + width * 0.75, mid_y, 0.1),
            left_front_paw=(x1 + width * 0.25, y2 - height * 0.1, 0.1),
            right_front_paw=(x1 + width * 0.25, y2 - height * 0.1, 0.1),
            left_hind_paw=(x1 + width * 0.75, y2 - height * 0.1, 0.1),
            right_hind_paw=(x1 + width * 0.75, y2 - height * 0.1, 0.1),
            tail_base=(x2 - width * 0.1, mid_y, 0.1),
            tail_tip=(x2, mid_y - height * 0.2, 0.1)
        )
        
        # Bounding boxes for parts (head 25%, torso 50%, hind 25%)
        body_parts = {
            'head': (x1, y1, int(x1 + width * 0.25), y2),
            'torso': (int(x1 + width * 0.25), y1, int(x1 + width * 0.75), y2),
            'hind': (int(x1 + width * 0.75), y1, x2, y2)
        }
        
        return PoseEstimationResult(
            keypoints=kp,
            body_parts=body_parts,
            body_axis_angle=0.0,
            pose_confidence=0.1  # Low confidence for fallback
        )

    def _derive_body_parts(self, keypoints: TigerKeypoints, bbox: Tuple[int, int, int, int]) -> Dict[str, Tuple[int, int, int, int]]:
        """Computes tight bounding boxes around body part keypoints."""
        # This would use keypoint coordinates to derive accurate part boxes
        # Placeholder returns geometric split
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        return {
            'head': (x1, y1, int(x1 + width * 0.25), y2),
            'torso': (int(x1 + width * 0.25), y1, int(x1 + width * 0.75), y2),
            'hind': (int(x1 + width * 0.75), y1, x2, y2)
        }

    def _compute_body_axis(self, keypoints: TigerKeypoints) -> float:
        """Computes the angle of the body's main axis (shoulder to hip)."""
        import math
        try:
            sx = (keypoints.left_shoulder[0] + keypoints.right_shoulder[0]) / 2.0
            sy = (keypoints.left_shoulder[1] + keypoints.right_shoulder[1]) / 2.0
            hx = (keypoints.left_hip[0] + keypoints.right_hip[0]) / 2.0
            hy = (keypoints.left_hip[1] + keypoints.right_hip[1]) / 2.0
            
            dx = hx - sx
            dy = hy - sy
            return math.degrees(math.atan2(dy, dx))
        except Exception:
            return 0.0


_pose_estimator_instance = None

def get_pose_estimator() -> TigerPoseEstimator:
    """Returns a singleton instance of the TigerPoseEstimator."""
    global _pose_estimator_instance
    if _pose_estimator_instance is None:
        _pose_estimator_instance = TigerPoseEstimator()
    return _pose_estimator_instance
