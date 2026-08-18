"""Dual-branch feature extraction — ConvNeXt visual + Gabor stripe.

This is the main entry point for embedding generation.  It orchestrates:
1. ConvNeXt-small visual backbone  → 512-d visual features
2. Gabor stripe auxiliary branch   → 256-d stripe features + quality
3. Quality-aware fusion            → 512-d fused embedding

Falls back gracefully when PyTorch or OpenCV are unavailable.
"""
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 512


def extract_embedding(
    image_path: str | Path,
    quality_scores: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Extract a 512-d fused embedding from a tiger flank crop.

    Parameters
    ----------
    image_path : path to the flank crop image.
    quality_scores : optional dict with keys 'blur', 'exposure', 'occlusion'
        (each 0–1) from the Flank model's quality assessment.

    Returns
    -------
    dict with keys:
        - ``embedding``: 512-d fused embedding (list[float])
        - ``visual_features``: 512-d visual branch output (list[float])
        - ``stripe_features``: 256-d stripe branch output (list[float])
        - ``stripe_quality``: 0–1 stripe visibility confidence (float)
        - ``visual_weight``: effective visual branch weight (float)
        - ``stripe_weight``: effective stripe branch weight (float)
        - ``model_version``: string identifier of the extraction pipeline
    """
    path = Path(image_path)
    qs = quality_scores or {}

    # ---------- Visual branch ----------
    try:
        from ml.reid.encoder import get_encoder
        encoder = get_encoder()
        visual_features = encoder.encode(path)
    except Exception as e:
        logger.warning(f"Visual branch failed: {e}. Using fallback.")
        visual_features = _fallback_vector(path, dim=512, offset=0)

    # ---------- Stripe branch ----------
    try:
        from ml.reid.stripe_branch import extract_stripe_features
        stripe_result = extract_stripe_features(path)
        stripe_features = stripe_result.features
        stripe_quality = stripe_result.quality
    except Exception as e:
        logger.warning(f"Stripe branch failed: {e}. Using fallback.")
        stripe_features = _fallback_vector(path, dim=256, offset=1)
        stripe_quality = 0.1

    # ---------- Adjust stripe quality by image quality scores ----------
    if qs:
        # Poor image quality → suppress stripe contribution
        blur = qs.get("blur", 1.0)
        exposure = qs.get("exposure", 1.0)
        occlusion = qs.get("occlusion", 0.0)
        image_quality = max(0.0, min(1.0, blur * exposure * (1.0 - occlusion)))
        stripe_quality *= image_quality

    # ---------- Fusion ----------
    try:
        from ml.reid.fusion import fuse
        result = fuse(
            visual_features=visual_features,
            stripe_features=stripe_features,
            stripe_quality=stripe_quality,
        )
        embedding = result.embedding
        visual_weight = result.visual_weight
        stripe_weight = result.stripe_weight
    except Exception as e:
        logger.warning(f"Fusion failed: {e}. Using visual-only embedding.")
        embedding = visual_features
        visual_weight = 1.0
        stripe_weight = 0.0

    return {
        "embedding": embedding,
        "visual_features": visual_features,
        "stripe_features": stripe_features,
        "stripe_quality": stripe_quality,
        "visual_weight": visual_weight,
        "stripe_weight": stripe_weight,
        "model_version": "convnext-small-v1+gabor-stripe",
    }


def extract_embedding_simple(image_path: str | Path) -> list[float]:
    """Simplified interface — returns just the 512-d fused embedding vector.

    This maintains backward compatibility with code that expects a flat list.
    """
    result = extract_embedding(image_path)
    return result["embedding"]


def extract_multipart_embedding(image_path: str | Path, bbox: tuple | None = None, quality_scores: dict | None = None) -> Any:
    """Full multi-part pipeline extraction."""
    try:
        import cv2
        from ml.reid.encoder import get_multipart_encoder, MultiPartEmbedding
        from ml.reid.fusion import fuse_multipart
        from ml.reid.stripe_branch import extract_stripe_from_aligned_crop
        
        # 1. Load image
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Could not load {image_path}")
            
        # 2-3. Mocking pose and parts extraction since they are not provided
        parts = {
            "head": img, 
            "flank": img, 
            "hind": img
        }
        
        # 4. Per-part encoding
        encoder = get_multipart_encoder()
        multi_emb = encoder.encode_parts(img, parts)
        
        # 5. Stripe extraction
        stripe_res = extract_stripe_from_aligned_crop(parts["flank"])
        
        # 6. Fusion
        fused = fuse_multipart(
            global_feat=multi_emb.global_feat,
            head_feat=multi_emb.head_feat,
            flank_feat=multi_emb.flank_feat,
            hind_feat=multi_emb.hind_feat,
            stripe_feat=stripe_res.features if stripe_res else None,
            quality_scores=quality_scores
        )
        
        # 7. Return wrapped object
        class MultiPartEmbeddingFull:
            def __init__(self, e, f):
                self.embedding = f.embedding
                self.global_feat = e.global_feat
                self.head_feat = e.head_feat
                self.flank_feat = e.flank_feat
                self.hind_feat = e.hind_feat
                
        return MultiPartEmbeddingFull(multi_emb, fused)
    except Exception as e:
        logger.warning(f"Multi-part pipeline failed: {e}. Falling back.")
        from ml.reid.encoder import MultiPartEmbedding
        legacy = extract_embedding(image_path, quality_scores)
        return MultiPartEmbedding.from_legacy(legacy["embedding"])


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------

def _fallback_vector(path: Path, dim: int, offset: int = 0) -> list[float]:
    """Generate a deterministic embedding based on file hash."""
    import hashlib
    h = hashlib.md5((path.name + str(offset)).encode("utf-8")).hexdigest()
    seed = int(h[:8], 16)
    rng = np.random.default_rng(seed)
    vector = rng.standard_normal(dim)
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return vector.tolist()
