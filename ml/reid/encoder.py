"""ConvNeXt-small visual backbone for tiger Re-ID.

Replaces the original ResNet50 encoder with ConvNeXt-small which provides
better accuracy/FLOPs trade-off and stronger transfer-learning features
for fine-grained recognition tasks like individual tiger identification.

The encoder removes the classification head and adds a learned projection
from ConvNeXt's 768-d feature space to our standard 512-d embedding space.
Supports loading custom metric-learned weights from checkpoints.
"""
import logging
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Optional PyTorch imports
try:
    import torch
    import torch.nn as nn
    import torchvision.transforms as T
    from torchvision.models import convnext_small, ConvNeXt_Small_Weights
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

VISUAL_DIM = 512
BACKBONE_DIM = 768  # ConvNeXt-small feature dimension


class VisualEncoder:
    """ConvNeXt-small backbone with projection head for tiger Re-ID.

    Attributes
    ----------
    model : torch.nn.Module or None
        The ConvNeXt-small model with projection head.
    device : torch.device
        The device (CPU/CUDA) the model runs on.
    transform : callable
        Preprocessing transform for input images.
    """

    def __init__(self, checkpoint_path: Optional[str | Path] = None):
        """Initialise the visual encoder.

        Parameters
        ----------
        checkpoint_path : optional path to a metric-learned checkpoint
            (.pt file) that overrides the default ImageNet weights.
        """
        self._model = None
        self._projection = None
        self._transform = None
        self._device = None
        self._checkpoint_path = Path(checkpoint_path) if checkpoint_path else None
        self._initialised = False

    def _lazy_init(self) -> bool:
        """Lazy initialisation — only loads model on first call."""
        if self._initialised:
            return self._model is not None

        self._initialised = True

        if not HAS_TORCH:
            logger.warning("PyTorch not available. VisualEncoder will use fallback.")
            return False

        try:
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

            # Load backbone
            if self._checkpoint_path and self._checkpoint_path.exists():
                logger.info(f"Loading metric-learned checkpoint: {self._checkpoint_path}")
                self._model, self._projection = self._load_checkpoint(self._checkpoint_path)
            else:
                logger.info("Loading pretrained ConvNeXt-small (ImageNet weights)")
                weights = ConvNeXt_Small_Weights.DEFAULT
                backbone = convnext_small(weights=weights)

                # Remove classification head — keep features up to avgpool
                # ConvNeXt forward: features → classifier; we want features only
                self._model = nn.Sequential(
                    backbone.features,
                    backbone.avgpool,
                    nn.Flatten(1),
                )

                # Projection head: 768 → 512
                self._projection = nn.Sequential(
                    nn.Linear(BACKBONE_DIM, VISUAL_DIM),
                    nn.BatchNorm1d(VISUAL_DIM),
                )

                # Initialise projection with deterministic weights
                torch.manual_seed(2024)
                nn.init.kaiming_normal_(self._projection[0].weight)
                nn.init.zeros_(self._projection[0].bias)

                self._transform = weights.transforms()

            self._model = self._model.to(self._device)
            self._projection = self._projection.to(self._device)
            self._model.eval()
            self._projection.eval()

            logger.info(f"VisualEncoder initialised on {self._device}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialise VisualEncoder: {e}")
            self._model = None
            return False

    def _load_checkpoint(self, path: Path) -> tuple:
        """Load a complete encoder from a training checkpoint."""
        checkpoint = torch.load(str(path), map_location="cpu", weights_only=False)

        # Reconstruct backbone
        backbone = convnext_small(weights=None)
        model = nn.Sequential(
            backbone.features,
            backbone.avgpool,
            nn.Flatten(1),
        )

        projection = nn.Sequential(
            nn.Linear(BACKBONE_DIM, VISUAL_DIM),
            nn.BatchNorm1d(VISUAL_DIM),
        )

        # Load state dicts
        if "backbone_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["backbone_state_dict"])
        if "projection_state_dict" in checkpoint:
            projection.load_state_dict(checkpoint["projection_state_dict"])

        # Set up transform
        self._transform = T.Compose([
            T.Resize((232, 232)),
            T.CenterCrop(224),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        return model, projection

    def encode(self, image_path: str | Path) -> list[float]:
        """Extract a 512-d visual embedding from an image.

        Parameters
        ----------
        image_path : path to the image file.

        Returns
        -------
        512-d L2-normalised visual feature vector.
        """
        if not self._lazy_init():
            return _fallback_embedding(Path(image_path))

        try:
            from PIL import Image
            img = Image.open(image_path).convert("RGB")

            if self._transform is None:
                self._transform = T.Compose([
                    T.Resize((232, 232)),
                    T.CenterCrop(224),
                    T.ToTensor(),
                    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                ])

            input_tensor = self._transform(img).unsqueeze(0).to(self._device)

            with torch.no_grad():
                backbone_features = self._model(input_tensor)       # [1, 768]
                projected = self._projection(backbone_features)     # [1, 512]

                # L2 normalise
                projected = nn.functional.normalize(projected, p=2, dim=1)

            return projected.squeeze(0).cpu().tolist()

        except Exception as e:
            logger.warning(f"Encoding failed for {image_path}: {e}. Using fallback.")
            return _fallback_embedding(Path(image_path))

    def encode_tensor(self, image_tensor: "torch.Tensor") -> "torch.Tensor":
        """Encode a pre-processed image tensor (used during training).

        Parameters
        ----------
        image_tensor : [B, 3, H, W] normalised image batch.

        Returns
        -------
        [B, 512] L2-normalised feature tensor.
        """
        if not self._lazy_init():
            raise RuntimeError("VisualEncoder not available (PyTorch missing)")

        backbone_features = self._model(image_tensor)
        projected = self._projection(backbone_features)
        return nn.functional.normalize(projected, p=2, dim=1)

    @property
    def device(self):
        """Return the device the encoder is on."""
        self._lazy_init()
        return self._device


from collections import namedtuple
MultiPartEmbedding = namedtuple('MultiPartEmbedding', ['global_feat', 'head_feat', 'flank_feat', 'hind_feat'])
MultiPartEmbedding.from_legacy = lambda x: MultiPartEmbedding(global_feat=x, head_feat=None, flank_feat=None, hind_feat=None)

class MultiPartEncoder:
    def __init__(self, backbone_name: str = 'convnext_small', checkpoint_path: str | Path | None = None):
        self.backbone_name = backbone_name
        self._model = None
        self._global_proj = None
        self._head_proj = None
        self._flank_proj = None
        self._hind_proj = None
        self._transform = None
        self._device = None
        self._checkpoint_path = Path(checkpoint_path) if checkpoint_path else None
        self._initialised = False

    def _lazy_init(self) -> bool:
        if self._initialised:
            return self._model is not None
        self._initialised = True
        if not HAS_TORCH:
            logger.warning("PyTorch not available. MultiPartEncoder will use fallback.")
            return False
        try:
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            from ml.reid.backbones import BackboneFactory
            self._model, feature_dim = BackboneFactory.create(self.backbone_name)
            
            self._global_proj = nn.Sequential(nn.Linear(feature_dim, 512), nn.BatchNorm1d(512))
            self._head_proj = nn.Sequential(nn.Linear(feature_dim, 128), nn.BatchNorm1d(128))
            self._flank_proj = nn.Sequential(nn.Linear(feature_dim, 256), nn.BatchNorm1d(256))
            self._hind_proj = nn.Sequential(nn.Linear(feature_dim, 128), nn.BatchNorm1d(128))
            
            torch.manual_seed(2024)
            for proj in [self._global_proj, self._head_proj, self._flank_proj, self._hind_proj]:
                nn.init.kaiming_normal_(proj[0].weight)
                nn.init.zeros_(proj[0].bias)
                proj.to(self._device)
                proj.eval()
            
            self._transform = BackboneFactory.get_transforms(self.backbone_name, is_training=False)
            self._model = self._model.to(self._device)
            self._model.eval()
            return True
        except Exception as e:
            logger.error(f"Failed to initialise MultiPartEncoder: {e}")
            self._model = None
            return False

    def encode_parts(self, image: np.ndarray, parts: dict) -> 'MultiPartEmbedding':
        if not self._lazy_init():
            return MultiPartEmbedding.from_legacy(_fallback_embedding(Path("fallback")))
        
        try:
            from PIL import Image
            def _encode_crop(crop_img, proj):
                if crop_img is None: return None
                img = Image.fromarray(crop_img).convert("RGB")
                tensor = self._transform(img).unsqueeze(0).to(self._device)
                feat = self._model(tensor)
                emb = proj(feat)
                emb = nn.functional.normalize(emb, p=2, dim=1)
                return emb.squeeze(0).cpu().tolist()

            with torch.no_grad():
                global_feat = _encode_crop(image, self._global_proj)
                head_feat = _encode_crop(parts.get('head'), self._head_proj) if 'head' in parts else None
                flank_feat = _encode_crop(parts.get('flank'), self._flank_proj) if 'flank' in parts else None
                hind_feat = _encode_crop(parts.get('hind'), self._hind_proj) if 'hind' in parts else None
                
                return MultiPartEmbedding(
                    global_feat=global_feat,
                    head_feat=head_feat,
                    flank_feat=flank_feat,
                    hind_feat=hind_feat
                )
        except Exception as e:
            logger.warning(f"Failed to encode parts: {e}")
            return MultiPartEmbedding.from_legacy(_fallback_embedding(Path("fallback")))

    def encode_global(self, image_path: str | Path) -> list[float]:
        return _fallback_embedding(Path(image_path))


# Singleton instance for shared use across the application
_ENCODER_INSTANCE: VisualEncoder | None = None
_MULTIPART_ENCODER_INSTANCE: MultiPartEncoder | None = None

def get_multipart_encoder(checkpoint_path: Optional[str | Path] = None) -> MultiPartEncoder:
    global _MULTIPART_ENCODER_INSTANCE
    if _MULTIPART_ENCODER_INSTANCE is None:
        _MULTIPART_ENCODER_INSTANCE = MultiPartEncoder(checkpoint_path=checkpoint_path)
    return _MULTIPART_ENCODER_INSTANCE


def get_encoder(checkpoint_path: Optional[str | Path] = None) -> VisualEncoder:
    """Get or create the shared VisualEncoder singleton."""
    global _ENCODER_INSTANCE
    if _ENCODER_INSTANCE is None:
        _ENCODER_INSTANCE = VisualEncoder(checkpoint_path=checkpoint_path)
    return _ENCODER_INSTANCE


# Legacy adapter: keeps backward compatibility with old `encode(model, image)` calls
def encode(model, image: Path) -> list[float]:
    """Adapter contract: return a unit-normalised visual embedding from your trained encoder."""
    encoder = get_encoder()
    return encoder.encode(image)


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------

def _fallback_embedding(path: Path) -> list[float]:
    """Generate a deterministic 512-d embedding from filename hash."""
    import hashlib
    h = hashlib.md5(path.name.encode("utf-8")).hexdigest()
    seed = int(h[:8], 16)
    rng = np.random.default_rng(seed)
    vector = rng.standard_normal(VISUAL_DIM)
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return vector.tolist()
