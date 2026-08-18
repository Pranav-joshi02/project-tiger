import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

@dataclass
class SpottedDeerResult:
    confidence: float
    fawn_body_ratio: float
    white_spot_score: float
    stripe_absence_score: float
    is_likely_deer: bool

class SpottedDeerAnalyzer:
    """Pixel-level visual feature analyzer for detecting Spotted Deer (Axis axis)."""

    def analyze(self, image_path: Path) -> SpottedDeerResult:
        """Main entry point to analyze an image for Spotted Deer features."""
        try:
            with Image.open(image_path) as raw_img:
                # Correct EXIF orientation
                img = ImageOps.exif_transpose(raw_img)
                img_rgb = img.convert("RGB")
                
                # Resize to a consistent thumbnail size for uniform patch analysis
                thumb = img_rgb.resize((128, 128))
                arr = np.array(thumb, dtype=np.float32)
                
                fawn_body_ratio = self._detect_fawn_body(arr)
                white_spot_score = self._detect_white_spots(arr)
                stripe_absence_score = self._check_no_stripes(arr)
                
                # Check for foliage context (browsers are often in green surroundings)
                r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
                foliage_mask = (g > (r * 1.05)) & (g > (b * 1.05)) & (g > 40)
                foliage_ratio = float(np.mean(foliage_mask))
                
                confidence = self._compute_confidence(fawn_body_ratio, white_spot_score, stripe_absence_score, foliage_ratio)
                is_likely_deer = confidence > 0.55
                
                return SpottedDeerResult(
                    confidence=confidence,
                    fawn_body_ratio=fawn_body_ratio,
                    white_spot_score=white_spot_score,
                    stripe_absence_score=stripe_absence_score,
                    is_likely_deer=is_likely_deer
                )
        except Exception as e:
            logger.warning(f"SpottedDeerAnalyzer failed on {image_path}: {e}")
            return SpottedDeerResult(
                confidence=0.0,
                fawn_body_ratio=0.0,
                white_spot_score=0.0,
                stripe_absence_score=0.0,
                is_likely_deer=False
            )

    def _detect_fawn_body(self, arr: np.ndarray) -> float:
        """Ratio of fawn/brown pixels representing the deer's body."""
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        # Fawn/tawny-brown color ranges
        fawn_mask = (r >= 160) & (r <= 220) & (g >= 120) & (g <= 170) & (b >= 60) & (b <= 120)
        return float(np.mean(fawn_mask))

    def _detect_white_spots(self, arr: np.ndarray) -> float:
        """Detect scattered white dots on brown background using local contrast."""
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        # High brightness regions
        white_mask = (r > 200) & (g > 200) & (b > 200)
        
        # Analyze grid for scattered spots
        spot_patches = 0
        total_patches = 0
        for py in range(0, 128, 16):
            for px in range(0, 128, 16):
                patch_white = float(np.mean(white_mask[py:py+16, px:px+16]))
                # White spots should be small relative to the patch size
                if 0.02 < patch_white < 0.20:
                    spot_patches += 1
                total_patches += 1
                
        # Normalize score
        return min(1.0, spot_patches / max(1, total_patches * 0.3))

    def _check_no_stripes(self, arr: np.ndarray) -> float:
        """Verify absence of dark stripe pattern (anti-tiger check)."""
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        # Dark pixels typical of tiger stripes
        dark_stripe_mask = (r < 75) & (g < 75) & (b < 75)
        stripe_ratio = float(np.mean(dark_stripe_mask))
        # Penalize confidence if excessive dark stripe-like pixels are found
        return max(0.0, 1.0 - (stripe_ratio * 10))

    def _compute_confidence(self, fawn_ratio: float, spot_score: float, no_stripe_score: float, foliage_ratio: float) -> float:
        """Compute final weighted confidence."""
        base_confidence = (fawn_ratio * 2.0) + (spot_score * 0.5) + (foliage_ratio * 0.2)
        # Apply penalty if stripe patterns are detected
        confidence = base_confidence * no_stripe_score
        return min(1.0, confidence)
