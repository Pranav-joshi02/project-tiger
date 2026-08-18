"""Body-part extraction and geometric normalization for tiger Re-ID.

Extracts head, torso/flank, and hind/tail regions from tiger crops using
pose keypoints when available, or geometric heuristics as fallback.
Also implements geometric stripe normalization following the principle
from the 2009 3D surface model research: normalize body geometry before
comparing stripe patterns.
"""
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Tuple, Optional

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

# Local imports
try:
    from .pose_estimator import PoseEstimationResult, TigerKeypoints
except ImportError:
    PoseEstimationResult = None
    TigerKeypoints = None


logger = logging.getLogger(__name__)


class BodyPart(Enum):
    """Enumeration of tiger body parts for Re-ID."""
    HEAD = "head"
    TORSO = "torso"
    HIND = "hind"
    FULL_BODY = "full_body"


@dataclass
class PartCrop:
    """Represents an extracted crop for a specific body part."""
    part: BodyPart
    crop: 'np.ndarray'
    bbox: Tuple[int, int, int, int]
    confidence: float
    is_pose_aligned: bool


class BodyPartExtractor:
    """Extracts semantic body parts from tiger images."""
    
    def __init__(self, target_sizes: Optional[Dict[BodyPart, Tuple[int, int]]] = None):
        if target_sizes is None:
            self.target_sizes = {
                BodyPart.HEAD: (128, 128),
                BodyPart.TORSO: (256, 128),
                BodyPart.HIND: (128, 128),
                BodyPart.FULL_BODY: (256, 128)
            }
        else:
            self.target_sizes = target_sizes

    def extract_parts(self, image: 'np.ndarray', bbox: Tuple[int, int, int, int], 
                      pose_result: Optional[PoseEstimationResult] = None) -> Dict[BodyPart, PartCrop]:
        """Extracts head, torso, and hind parts from a tiger image."""
        if not HAS_NUMPY or not HAS_CV2:
            logger.error("NumPy and OpenCV are required for body part extraction.")
            return {}
            
        if pose_result is not None and pose_result.pose_confidence > 0.5:
            return self._extract_with_pose(image, bbox, pose_result)
        else:
            return self._extract_geometric(image, bbox)

    def _extract_with_pose(self, image: 'np.ndarray', bbox: Tuple[int, int, int, int], 
                           pose_result: PoseEstimationResult) -> Dict[BodyPart, PartCrop]:
        """Extracts parts using pose-derived bounding boxes."""
        parts = {}
        part_mapping = {
            'head': BodyPart.HEAD,
            'torso': BodyPart.TORSO,
            'hind': BodyPart.HIND
        }
        
        for part_str, part_bbox in pose_result.body_parts.items():
            if part_str in part_mapping:
                b_part = part_mapping[part_str]
                px1, py1, px2, py2 = part_bbox
                
                # Ensure within image bounds
                h, w = image.shape[:2]
                px1 = max(0, min(px1, w-1))
                py1 = max(0, min(py1, h-1))
                px2 = max(0, min(px2, w))
                py2 = max(0, min(py2, h))
                
                if px2 > px1 and py2 > py1:
                    crop = image[py1:py2, px1:px2]
                    resized_crop = self._resize_crop(crop, self.target_sizes[b_part])
                    
                    parts[b_part] = PartCrop(
                        part=b_part,
                        crop=resized_crop,
                        bbox=(px1, py1, px2, py2),
                        confidence=pose_result.pose_confidence,
                        is_pose_aligned=True
                    )
        
        # Add full body as well
        x1, y1, x2, y2 = bbox
        fb_crop = image[max(0, y1):y2, max(0, x1):x2]
        if fb_crop.size > 0:
            parts[BodyPart.FULL_BODY] = PartCrop(
                part=BodyPart.FULL_BODY,
                crop=self._resize_crop(fb_crop, self.target_sizes[BodyPart.FULL_BODY]),
                bbox=bbox,
                confidence=1.0,
                is_pose_aligned=False
            )
            
        return parts

    def _extract_geometric(self, image: 'np.ndarray', bbox: Tuple[int, int, int, int]) -> Dict[BodyPart, PartCrop]:
        """Extracts parts using geometric splitting (fallback)."""
        parts = {}
        x1, y1, x2, y2 = bbox
        
        # Ensure within bounds
        h, w = image.shape[:2]
        x1 = max(0, min(x1, w-1))
        y1 = max(0, min(y1, h-1))
        x2 = max(0, min(x2, w))
        y2 = max(0, min(y2, h))
        
        if x2 <= x1 or y2 <= y1:
            return parts
            
        width = x2 - x1
        
        # Head (25%)
        hx1, hy1, hx2, hy2 = x1, y1, int(x1 + width * 0.25), y2
        if hx2 > hx1 and hy2 > hy1:
            head_crop = image[hy1:hy2, hx1:hx2]
            parts[BodyPart.HEAD] = PartCrop(
                part=BodyPart.HEAD,
                crop=self._resize_crop(head_crop, self.target_sizes[BodyPart.HEAD]),
                bbox=(hx1, hy1, hx2, hy2),
                confidence=0.1,
                is_pose_aligned=False
            )
            
        # Torso (50%)
        tx1, ty1, tx2, ty2 = int(x1 + width * 0.25), y1, int(x1 + width * 0.75), y2
        if tx2 > tx1 and ty2 > ty1:
            torso_crop = image[ty1:ty2, tx1:tx2]
            parts[BodyPart.TORSO] = PartCrop(
                part=BodyPart.TORSO,
                crop=self._resize_crop(torso_crop, self.target_sizes[BodyPart.TORSO]),
                bbox=(tx1, ty1, tx2, ty2),
                confidence=0.1,
                is_pose_aligned=False
            )
            
        # Hind (25%)
        nx1, ny1, nx2, ny2 = int(x1 + width * 0.75), y1, x2, y2
        if nx2 > nx1 and ny2 > ny1:
            hind_crop = image[ny1:ny2, nx1:nx2]
            parts[BodyPart.HIND] = PartCrop(
                part=BodyPart.HIND,
                crop=self._resize_crop(hind_crop, self.target_sizes[BodyPart.HIND]),
                bbox=(nx1, ny1, nx2, ny2),
                confidence=0.1,
                is_pose_aligned=False
            )
            
        # Full Body
        fb_crop = image[y1:y2, x1:x2]
        parts[BodyPart.FULL_BODY] = PartCrop(
            part=BodyPart.FULL_BODY,
            crop=self._resize_crop(fb_crop, self.target_sizes[BodyPart.FULL_BODY]),
            bbox=bbox,
            confidence=1.0,
            is_pose_aligned=False
        )
            
        return parts

    def _resize_crop(self, crop: 'np.ndarray', target_size: Tuple[int, int]) -> 'np.ndarray':
        """Resizes crop to target size."""
        if not HAS_CV2:
            return crop
        return cv2.resize(crop, target_size, interpolation=cv2.INTER_LINEAR)


class GeometricStripeNormalizer:
    """Normalizes body geometry for consistent stripe extraction."""
    
    def __init__(self):
        pass
        
    def normalize(self, torso_crop: 'np.ndarray', body_axis_angle: float = 0.0, 
                  keypoints: Optional[TigerKeypoints] = None) -> 'np.ndarray':
        """Rotates torso to horizontal and applies affine transform."""
        if not HAS_CV2 or torso_crop.size == 0:
            return torso_crop
            
        # First rotate to horizontal if needed
        if abs(body_axis_angle) > 5.0:
            torso_crop = self._rotate_to_horizontal(torso_crop, body_axis_angle)
            
        # If we have precise keypoints, we can do affine transform
        if keypoints is not None:
            h, w = torso_crop.shape[:2]
            M = self._compute_affine_transform(keypoints, w, h)
            if M is not None:
                torso_crop = cv2.warpAffine(torso_crop, M, (w, h))
                
        return torso_crop

    def _compute_affine_transform(self, keypoints: TigerKeypoints, 
                                  target_width: int, target_height: int) -> Optional['np.ndarray']:
        """Computes a 2x3 affine matrix for normalizing perspective."""
        # Advanced normalization based on 3D surface model principles
        # This is a simplified placeholder
        if not HAS_CV2:
            return None
            
        # In practice, map shoulder/hip points to a canonical rectangle
        try:
            src_pts = np.float32([
                [keypoints.left_shoulder[0], keypoints.left_shoulder[1]],
                [keypoints.left_hip[0], keypoints.left_hip[1]],
                [keypoints.right_shoulder[0], keypoints.right_shoulder[1]]
            ])
            dst_pts = np.float32([
                [target_width * 0.2, target_height * 0.3],
                [target_width * 0.8, target_height * 0.3],
                [target_width * 0.2, target_height * 0.7]
            ])
            return cv2.getAffineTransform(src_pts, dst_pts)
        except Exception:
            return None

    def _rotate_to_horizontal(self, crop: 'np.ndarray', angle: float) -> 'np.ndarray':
        """Simple rotation to align the body axis horizontally."""
        if not HAS_CV2:
            return crop
            
        h, w = crop.shape[:2]
        center = (w // 2, h // 2)
        
        # Negative angle because image y-axis goes down
        M = cv2.getRotationMatrix2D(center, -angle, 1.0)
        return cv2.warpAffine(crop, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
