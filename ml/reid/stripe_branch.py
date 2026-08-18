"""Stripe Auxiliary Branch — structural feature extraction from tiger flanks.

This module implements a classical computer-vision pipeline that extracts
stripe-pattern features from tiger flank crops.  The stripe branch runs
alongside the visual (ConvNeXt) branch and the two are fused via
quality-aware concatenation in `fusion.py`.

Pipeline:
    Flank crop → Resize → Illumination normalisation → Contrast normalisation
    → Background suppression → Stripe enhancement (Gabor filter bank)
    → Structural representation → 256-d feature vector + quality score
"""
import logging
import math
from pathlib import Path
from typing import NamedTuple

import numpy as np

logger = logging.getLogger(__name__)

# Optional OpenCV import — falls back to dummy features if missing
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

STRIPE_DIM = 256


class StripeResult(NamedTuple):
    """Output of stripe feature extraction."""
    features: list[float]     # 256-d stripe feature vector (L2-normalised)
    quality: float            # 0–1 confidence in stripe visibility


def extract_stripe_features(
    image_path: str | Path,
    target_size: tuple[int, int] = (256, 128),
) -> StripeResult:
    """Extract stripe structural features from a tiger flank crop.

    Parameters
    ----------
    image_path : path to the flank crop image.
    target_size : (width, height) to resize the crop before processing.

    Returns
    -------
    StripeResult with 256-d feature vector and quality score.
    """
    path = Path(image_path)

    if not HAS_CV2:
        logger.warning("OpenCV not installed — generating dummy stripe features.")
        return _dummy_stripe_features(path)

    try:
        img = cv2.imread(str(path))
        if img is None:
            logger.warning(f"Cannot read image {path}. Falling back to dummy.")
            return _dummy_stripe_features(path)

        # 1. Resize
        img = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)

        # 2. Convert to grayscale + illumination normalisation (CLAHE)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = _illumination_normalise(gray)

        # 3. Contrast normalisation
        gray = _contrast_normalise(gray)

        # 4. Background suppression via simple Otsu masking
        mask = _suppress_background(gray)
        gray_masked = cv2.bitwise_and(gray, gray, mask=mask)

        # 5. Gabor filter bank → stripe-enhanced response maps
        responses = _gabor_filter_bank(gray_masked)

        # 6. Structural representation — histogram + spatial stats
        features = _structural_representation(responses, mask)

        # 7. Quality assessment
        quality = _assess_stripe_quality(responses, mask)

        return StripeResult(features=features, quality=quality)

    except Exception as e:
        logger.warning(f"Stripe extraction failed for {path}: {e}. Falling back to dummy.")
        return _dummy_stripe_features(path)


def extract_stripe_from_aligned_crop(aligned_crop: "np.ndarray", body_axis_angle: float = 0.0) -> StripeResult:
    """Extract stripe structural features from an aligned torso crop.

    Parameters
    ----------
    aligned_crop : pose-aligned torso crop
    body_axis_angle : float, angle for geometric normalisation correction

    Returns
    -------
    StripeResult
    """
    if not HAS_CV2:
        return StripeResult(features=[0.0]*STRIPE_DIM, quality=0.0)
        
    try:
        # Apply geometric normalization correction
        if abs(body_axis_angle) > 1e-3:
            h, w = aligned_crop.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, body_axis_angle, 1.0)
            aligned_crop = cv2.warpAffine(aligned_crop, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            
        target_size = (256, 128)
        img = cv2.resize(aligned_crop, target_size, interpolation=cv2.INTER_AREA)
        
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
            
        gray = _illumination_normalise(gray)
        gray = _contrast_normalise(gray)
        mask = _suppress_background(gray)
        gray_masked = cv2.bitwise_and(gray, gray, mask=mask)
        responses = _gabor_filter_bank(gray_masked)
        features = _structural_representation(responses, mask)
        quality = _assess_stripe_quality(responses, mask)
        
        return StripeResult(features=features, quality=quality)
    except Exception as e:
        logger.warning(f"Stripe extraction failed on aligned crop: {e}")
        return StripeResult(features=[0.0]*STRIPE_DIM, quality=0.0)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _illumination_normalise(gray: "np.ndarray") -> "np.ndarray":
    """Apply CLAHE (Contrast Limited Adaptive Histogram Equalisation)."""
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def _contrast_normalise(gray: "np.ndarray") -> "np.ndarray":
    """Zero-mean, unit-variance normalisation clipped to [0, 255]."""
    mean = gray.mean()
    std = gray.std() + 1e-6
    normalised = ((gray.astype(np.float32) - mean) / std) * 50 + 128
    return np.clip(normalised, 0, 255).astype(np.uint8)


def _suppress_background(gray: "np.ndarray") -> "np.ndarray":
    """Produce a binary mask that keeps the foreground tiger body."""
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Morphological close to fill holes
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    return mask


def _gabor_filter_bank(
    gray: "np.ndarray",
    num_orientations: int = 8,
    wavelengths: tuple[float, ...] = (4.0, 6.0, 8.0, 12.0),
) -> list["np.ndarray"]:
    """Apply a bank of Gabor filters at multiple orientations and scales.

    Returns a list of response magnitude images.
    """
    responses = []
    for wavelength in wavelengths:
        for i in range(num_orientations):
            theta = i * math.pi / num_orientations
            kernel = cv2.getGaborKernel(
                ksize=(21, 21),
                sigma=wavelength * 0.56,
                theta=theta,
                lambd=wavelength,
                gamma=0.5,
                psi=0,
                ktype=cv2.CV_32F,
            )
            filtered = cv2.filter2D(gray, cv2.CV_32F, kernel)
            responses.append(np.abs(filtered))
    return responses


def _structural_representation(
    responses: list["np.ndarray"],
    mask: "np.ndarray",
    num_spatial_bins: int = 4,
) -> list[float]:
    """Convert Gabor response maps into a fixed-size feature vector.

    For each response map we compute:
      - Mean and std of the masked region (global stats)
      - Spatial histogram: divide the image into horizontal strips and
        compute mean energy per strip (captures vertical position of stripes)

    Total feature dimension = len(responses) * (2 + num_spatial_bins)
    We then project to 256-d via PCA-like deterministic hashing if needed.
    """
    raw_features: list[float] = []
    mask_bool = mask > 0

    for resp in responses:
        masked_vals = resp[mask_bool] if mask_bool.any() else resp.flatten()

        # Global stats
        raw_features.append(float(np.mean(masked_vals)))
        raw_features.append(float(np.std(masked_vals)))

        # Spatial bins (horizontal strips)
        h = resp.shape[0]
        strip_h = max(h // num_spatial_bins, 1)
        for b in range(num_spatial_bins):
            y_start = b * strip_h
            y_end = min((b + 1) * strip_h, h)
            strip = resp[y_start:y_end]
            strip_mask = mask[y_start:y_end] > 0
            if strip_mask.any():
                raw_features.append(float(np.mean(strip[strip_mask])))
            else:
                raw_features.append(0.0)

    # Project to STRIPE_DIM via deterministic linear mapping
    raw = np.array(raw_features, dtype=np.float32)
    features = _project_to_dim(raw, STRIPE_DIM)

    # L2 normalise
    norm = np.linalg.norm(features)
    if norm > 0:
        features = features / norm

    return features.tolist()


def _project_to_dim(raw: "np.ndarray", target_dim: int) -> "np.ndarray":
    """Deterministic projection to target_dim using a seeded random matrix."""
    rng = np.random.default_rng(seed=42)
    if len(raw) == target_dim:
        return raw
    elif len(raw) > target_dim:
        # Truncated random projection
        proj = rng.standard_normal((target_dim, len(raw))).astype(np.float32)
        proj /= np.linalg.norm(proj, axis=1, keepdims=True)
        return proj @ raw
    else:
        # Pad with zeros then project
        padded = np.zeros(target_dim, dtype=np.float32)
        padded[: len(raw)] = raw
        return padded


def _assess_stripe_quality(
    responses: list["np.ndarray"],
    mask: "np.ndarray",
) -> float:
    """Estimate how clearly visible the stripe pattern is (0–1).

    High quality → strong directional response energy within the mask.
    Low quality → uniform/noisy response (IR images, heavy blur, occlusion).
    """
    if not responses:
        return 0.0

    mask_bool = mask > 0
    if not mask_bool.any():
        return 0.0

    # Compute mean energy across all orientations/scales
    energies = [float(np.mean(r[mask_bool])) for r in responses]
    mean_energy = np.mean(energies)
    max_energy = np.max(energies)

    # Directional selectivity: ratio of max to mean
    # High ratio → stripes have a clear preferred orientation
    selectivity = (max_energy / (mean_energy + 1e-6)) - 1.0

    # Normalise to 0–1 range (empirical calibration)
    quality = min(1.0, max(0.0, selectivity / 3.0))

    # Also penalise very low overall energy (blank/dark images)
    if mean_energy < 5.0:
        quality *= 0.3

    return float(quality)


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------

def _dummy_stripe_features(path: Path) -> StripeResult:
    """Generate deterministic dummy stripe features based on filename hash."""
    import hashlib
    h = hashlib.md5(path.name.encode("utf-8")).hexdigest()
    seed = int(h[:8], 16)
    rng = np.random.default_rng(seed)
    vector = rng.standard_normal(STRIPE_DIM).astype(np.float64)
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return StripeResult(features=vector.tolist(), quality=0.3)
