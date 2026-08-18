"""Quality-aware feature fusion — merges visual and stripe branches.

Combines the ConvNeXt visual embedding with the Gabor stripe features using
quality-weighted concatenation and deterministic projection to 512-d.

When stripe quality is high (clear daylight flank image), the stripe branch
contributes strongly.  When stripe quality is low (IR/blur/occlusion), the
stripe contribution is suppressed and the visual branch dominates.
"""
import logging
from typing import NamedTuple

import numpy as np

logger = logging.getLogger(__name__)

FUSED_DIM = 512
VISUAL_DIM = 512
STRIPE_DIM = 256


class FusionResult(NamedTuple):
    """Output of dual-branch feature fusion."""
    embedding: list[float]       # 512-d fused embedding (L2-normalised)
    visual_weight: float         # effective weight of visual branch
    stripe_weight: float         # effective weight of stripe branch


def fuse(
    visual_features: list[float],
    stripe_features: list[float],
    stripe_quality: float,
    visual_quality: float = 1.0,
    min_stripe_weight: float = 0.05,
    max_stripe_weight: float = 0.40,
) -> FusionResult:
    """Quality-weighted fusion of visual and stripe feature branches.

    Parameters
    ----------
    visual_features : 512-d visual embedding from ConvNeXt backbone.
    stripe_features : 256-d stripe features from Gabor pipeline.
    stripe_quality : 0–1 confidence in stripe visibility.
    visual_quality : 0–1 overall image quality (blur/exposure composite).
    min_stripe_weight : minimum contribution of stripe branch.
    max_stripe_weight : maximum contribution of stripe branch.

    Returns
    -------
    FusionResult with 512-d fused embedding and effective branch weights.
    """
    v = np.array(visual_features, dtype=np.float64)
    s = np.array(stripe_features, dtype=np.float64)

    # Validate dimensions
    if len(v) != VISUAL_DIM:
        logger.warning(f"Visual features dim {len(v)} != {VISUAL_DIM}. Padding/truncating.")
        v = _resize_vector(v, VISUAL_DIM)
    if len(s) != STRIPE_DIM:
        logger.warning(f"Stripe features dim {len(s)} != {STRIPE_DIM}. Padding/truncating.")
        s = _resize_vector(s, STRIPE_DIM)

    # Compute effective stripe weight from quality
    # Linear interpolation between min and max based on stripe quality
    stripe_quality_clamped = max(0.0, min(1.0, stripe_quality))
    stripe_weight = min_stripe_weight + (max_stripe_weight - min_stripe_weight) * stripe_quality_clamped
    visual_weight = 1.0 - stripe_weight

    # Apply quality weighting
    weighted_visual = visual_weight * v
    weighted_stripe = stripe_weight * s

    # Concatenate: [visual(512) | stripe(256)] → 768-d
    concatenated = np.concatenate([weighted_visual, weighted_stripe])

    # Project to 512-d using a deterministic random projection matrix
    fused = _project_to_fused_dim(concatenated)

    # L2 normalise the final embedding
    norm = np.linalg.norm(fused)
    if norm > 0:
        fused = fused / norm

    return FusionResult(
        embedding=fused.tolist(),
        visual_weight=float(visual_weight),
        stripe_weight=float(stripe_weight),
    )


def fuse_visual_only(visual_features: list[float]) -> FusionResult:
    """Produce a fused embedding using only the visual branch.

    Used when stripe extraction fails or is not applicable (e.g. frontal view).
    """
    v = np.array(visual_features, dtype=np.float64)
    if len(v) != VISUAL_DIM:
        v = _resize_vector(v, VISUAL_DIM)

    # Zero-pad stripe portion
    zeros = np.zeros(STRIPE_DIM, dtype=np.float64)
    concatenated = np.concatenate([v, zeros])
    fused = _project_to_fused_dim(concatenated)

    norm = np.linalg.norm(fused)
    if norm > 0:
        fused = fused / norm

    return FusionResult(embedding=fused.tolist(), visual_weight=1.0, stripe_weight=0.0)


def fuse_multipart(global_feat, head_feat, flank_feat, hind_feat, stripe_feat, quality_scores: dict | None = None, weights: dict | None = None) -> FusionResult:
    """Multi-part feature fusion."""
    weights = weights or {"global": 0.30, "flank": 0.40, "head": 0.15, "hind": 0.15}
    
    parts = {
        "global": (global_feat, 512),
        "flank": (flank_feat, 256),
        "head": (head_feat, 128),
        "hind": (hind_feat, 128)
    }
    
    # Handle missing parts by redistributing weights
    missing = [k for k, (v, _) in parts.items() if v is None]
    available = [k for k in parts.keys() if k not in missing]
    
    if not available:
        # Fallback to zeros
        return FusionResult(embedding=np.zeros(512).tolist(), visual_weight=0.0, stripe_weight=0.0)
        
    missing_weight = sum(weights[k] for k in missing)
    if missing_weight > 0 and available:
        extra_per_part = missing_weight / len(available)
        for k in available:
            weights[k] += extra_per_part
            
    concat_list = []
    
    # Gather visual parts
    for k in ["global", "head", "flank", "hind"]:
        feat, expected_dim = parts[k]
        if feat is not None:
            v = np.array(feat, dtype=np.float64)
            if len(v) != expected_dim:
                v = _resize_vector(v, expected_dim)
            concat_list.append(v * weights[k])
            
    # Stripe part
    if stripe_feat is not None:
        s = np.array(stripe_feat, dtype=np.float64)
        if len(s) != STRIPE_DIM:
            s = _resize_vector(s, STRIPE_DIM)
        stripe_quality = quality_scores.get('stripe', 1.0) if quality_scores else 1.0
        # Incorporate stripe quality into its contribution
        concat_list.append(s * stripe_quality)
        stripe_weight = stripe_quality
    else:
        stripe_weight = 0.0
        
    concatenated = np.concatenate(concat_list)
    
    # We need a new projection matrix for the multi-part size
    proj_dim = len(concatenated)
    rng = np.random.default_rng(seed=2024 + proj_dim)
    raw = rng.standard_normal((proj_dim, FUSED_DIM)).astype(np.float64)
    q, _ = np.linalg.qr(raw)
    proj = q[:, :FUSED_DIM]
    
    fused = concatenated @ proj
    norm = np.linalg.norm(fused)
    if norm > 0:
        fused = fused / norm
        
    return FusionResult(embedding=fused.tolist(), visual_weight=1.0 - stripe_weight, stripe_weight=stripe_weight)


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

# Cached projection matrix (initialised lazily)
_PROJ_MATRIX: np.ndarray | None = None
_CONCAT_DIM = VISUAL_DIM + STRIPE_DIM  # 768


def _get_projection_matrix() -> np.ndarray:
    """Get or create the deterministic 768→512 random projection matrix."""
    global _PROJ_MATRIX
    if _PROJ_MATRIX is None:
        rng = np.random.default_rng(seed=2024)
        # Gaussian random projection, orthogonalised for stability
        raw = rng.standard_normal((_CONCAT_DIM, FUSED_DIM)).astype(np.float64)
        # QR decomposition for near-orthogonal columns
        q, _ = np.linalg.qr(raw)
        _PROJ_MATRIX = q[:, :FUSED_DIM]  # (_CONCAT_DIM, FUSED_DIM)
    return _PROJ_MATRIX


def _project_to_fused_dim(concatenated: np.ndarray) -> np.ndarray:
    """Project a 768-d vector to 512-d via deterministic random projection."""
    proj = _get_projection_matrix()
    return concatenated @ proj  # (768,) @ (768, 512) → (512,)


def _resize_vector(v: np.ndarray, target_dim: int) -> np.ndarray:
    """Resize a vector to target dimension by truncating or zero-padding."""
    if len(v) >= target_dim:
        return v[:target_dim]
    padded = np.zeros(target_dim, dtype=v.dtype)
    padded[: len(v)] = v
    return padded
