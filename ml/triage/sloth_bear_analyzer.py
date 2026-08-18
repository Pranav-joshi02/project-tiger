import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps, ImageFilter

logger = logging.getLogger(__name__)

@dataclass
class SlothBearResult:
    confidence: float
    dark_fur_ratio: float
    chest_marking_score: float
    fur_texture_score: float
    is_ir_nighttime: bool
    is_likely_bear: bool

class SlothBearAnalyzer:
    """Pixel-level visual feature analyzer for detecting Sloth Bears (Melursus ursinus)."""
    
    def analyze(self, image_path: Path) -> SlothBearResult:
        """Main entry point to analyze an image for Sloth Bear features."""
        try:
            with Image.open(image_path) as raw_img:
                # Correct EXIF orientation
                img = ImageOps.exif_transpose(raw_img)
                img_rgb = img.convert("RGB")
                
                # Resize to a consistent thumbnail size
                thumb = img_rgb.resize((128, 128))
                arr = np.array(thumb, dtype=np.float32)
                
                # Detect grayscale/IR images based on color variance
                r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
                color_variance = np.mean(np.var(arr, axis=2))
                is_ir_nighttime = bool(color_variance < 10)
                
                # Anti-tiger check: Tiger orange/tawny fur & stripes
                tiger_warm_mask = (r > 100) & (g > 45) & (g < 195) & (b < 145) & ((r - b) > 25) & (r > g)
                tiger_warm_ratio = float(np.mean(tiger_warm_mask))
                dark_stripe_mask = (r < 75) & (g < 75) & (b < 75)
                stripe_ratio = float(np.mean(dark_stripe_mask))

                # If strong tiger orange and stripes or high tiger warm ratio, zero out bear confidence
                if (tiger_warm_ratio > 0.05 and stripe_ratio > 0.02) or tiger_warm_ratio > 0.12:
                    no_tiger_score = 0.0
                else:
                    no_tiger_score = max(0.0, 1.0 - (tiger_warm_ratio * 8.0))

                dark_fur_ratio = self._detect_dark_fur(arr, is_ir_nighttime)
                chest_marking_score = self._detect_chest_marking(arr, dark_fur_ratio, is_ir_nighttime)
                fur_texture_score = self._analyze_fur_texture(thumb)

                confidence = self._compute_confidence(
                    dark_fur_ratio, chest_marking_score, fur_texture_score, is_ir_nighttime, no_tiger_score
                )
                is_likely_bear = bool(confidence > 0.50 and no_tiger_score > 0.3)
                
                return SlothBearResult(
                    confidence=confidence,
                    dark_fur_ratio=dark_fur_ratio,
                    chest_marking_score=chest_marking_score,
                    fur_texture_score=fur_texture_score,
                    is_ir_nighttime=is_ir_nighttime,
                    is_likely_bear=is_likely_bear
                )
        except Exception as e:
            logger.warning(f"SlothBearAnalyzer failed on {image_path}: {e}")
            return SlothBearResult(
                confidence=0.0,
                dark_fur_ratio=0.0,
                chest_marking_score=0.0,
                fur_texture_score=0.0,
                is_ir_nighttime=False,
                is_likely_bear=False
            )

    def _detect_dark_fur(self, arr: np.ndarray, is_ir: bool = False) -> float:
        """Ratio of very dark pixels indicating dark/black fur (excluding dark green foliage)."""
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        if is_ir:
            gray = np.mean(arr, axis=2)
            dark_mask = gray < 80
        else:
            foliage_mask = (g > (r * 1.15)) & (g > (b * 1.15)) & (g > 35)
            dark_mask = (r < 75) & (g < 75) & (b < 75) & (~foliage_mask)
        return float(np.mean(dark_mask))

    def _detect_chest_marking(self, arr: np.ndarray, dark_fur_ratio: float = 0.0, is_ir: bool = False) -> float:
        """Detect bright V/Y-shaped patch in upper-center region of the dark body."""
        if dark_fur_ratio < 0.20:
            return 0.0
        h, w = arr.shape[:2]
        # Focus on upper-center chest region
        chest_region = arr[int(h*0.25):int(h*0.65), int(w*0.25):int(w*0.75)]
        
        if is_ir:
            chest_bright = np.mean(chest_region) > 90
            return float(np.mean(np.mean(chest_region, axis=2) > 110)) * 2.0 if chest_bright else 0.0
            
        # Searching for a cream/white contrast (neutral tone, not orange)
        cr, cg, cb = chest_region[:, :, 0], chest_region[:, :, 1], chest_region[:, :, 2]
        bright_mask = (cr > 160) & (cg > 150) & (cb > 120) & (abs(cr - cg) < 50)
        
        # Increase score if bright mask exists within reasonable range
        bright_ratio = float(np.mean(bright_mask))
        if 0.02 < bright_ratio < 0.35:
            return min(1.0, bright_ratio * 4.0)
        return 0.0

    def _analyze_fur_texture(self, img: Image.Image) -> float:
        """Edge density score for shaggy fur."""
        gray = img.convert("L")
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_arr = np.array(edges, dtype=np.float32)
        
        # Higher density of strong edges implies rough/shaggy fur
        edge_density = float(np.mean(edge_arr > 50))
        return min(1.0, edge_density * 2.0)

    def _detect_ir_dark_mass(self, arr: np.ndarray) -> bool:
        """Special handler for grayscale IR night images to find dark silhouettes."""
        return self._detect_dark_fur(arr, is_ir=True) > 0.3

    def _compute_confidence(self, dark_ratio: float, chest_score: float, texture_score: float, is_ir_nighttime: bool, no_tiger_score: float = 1.0) -> float:
        """Compute final weighted confidence."""
        if no_tiger_score <= 0.05:
            return 0.0
        if is_ir_nighttime:
            if dark_ratio < 0.20:
                return 0.0
            conf = min(1.0, (dark_ratio / 0.40) * 0.80 + (chest_score * 0.20))
            return min(1.0, conf * no_tiger_score)
            
        if dark_ratio < 0.20:
            return 0.0
        base_confidence = (min(1.0, dark_ratio / 0.45) * 0.55) + (chest_score * 0.30) + (texture_score * 0.15)
        return min(1.0, base_confidence * no_tiger_score)
