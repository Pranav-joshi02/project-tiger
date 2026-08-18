"""Backbone factory for tiger Re-ID model benchmarking.

Provides a unified interface to create and configure different CNN/Transformer
backbones for the Re-ID pipeline. Supports ablation studies comparing
ResNet50, EfficientNetV2, ConvNeXt-Small, ViT-B/16, and hybrid architectures.
"""
from dataclasses import dataclass
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import torchvision.transforms as T
    from torchvision.models import (
        resnet50, ResNet50_Weights,
        efficientnet_v2_s, EfficientNet_V2_S_Weights,
        convnext_small, ConvNeXt_Small_Weights,
        vit_b_16, ViT_B_16_Weights
    )
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

@dataclass
class BackboneConfig:
    name: str
    feature_dim: int
    input_size: int = 224
    pretrained: bool = True

BACKBONE_REGISTRY = {
    'resnet50': BackboneConfig(name='resnet50', feature_dim=2048, input_size=224),
    'efficientnetv2_s': BackboneConfig(name='efficientnetv2_s', feature_dim=1280, input_size=224),
    'convnext_small': BackboneConfig(name='convnext_small', feature_dim=768, input_size=224),
    'vit_b_16': BackboneConfig(name='vit_b_16', feature_dim=768, input_size=224),
    'convnext_vit_fusion': BackboneConfig(name='convnext_vit_fusion', feature_dim=1536, input_size=224),
}

class BackboneFactory:
    
    @staticmethod
    def create(name: str, pretrained: bool = True) -> tuple:
        if not HAS_TORCH:
            raise RuntimeError("PyTorch is not available.")
            
        config = BackboneFactory.get_config(name)
        
        if name == 'resnet50':
            weights = ResNet50_Weights.DEFAULT if pretrained else None
            backbone = resnet50(weights=weights)
            # Remove FC
            model = nn.Sequential(*list(backbone.children())[:-1], nn.Flatten(1))
            
        elif name == 'efficientnetv2_s':
            weights = EfficientNet_V2_S_Weights.DEFAULT if pretrained else None
            backbone = efficientnet_v2_s(weights=weights)
            # Remove classifier
            model = nn.Sequential(backbone.features, backbone.avgpool, nn.Flatten(1))
            
        elif name == 'convnext_small':
            weights = ConvNeXt_Small_Weights.DEFAULT if pretrained else None
            backbone = convnext_small(weights=weights)
            model = nn.Sequential(backbone.features, backbone.avgpool, nn.Flatten(1))
            
        elif name == 'vit_b_16':
            weights = ViT_B_16_Weights.DEFAULT if pretrained else None
            backbone = vit_b_16(weights=weights)
            # ViT is different, we can just use it and remove the head
            backbone.heads = nn.Identity()
            model = backbone
            
        elif name == 'convnext_vit_fusion':
            convnext_weights = ConvNeXt_Small_Weights.DEFAULT if pretrained else None
            convnext_model = convnext_small(weights=convnext_weights)
            convnext_part = nn.Sequential(convnext_model.features, convnext_model.avgpool, nn.Flatten(1))
            
            vit_weights = ViT_B_16_Weights.DEFAULT if pretrained else None
            vit_model = vit_b_16(weights=vit_weights)
            vit_model.heads = nn.Identity()
            
            class FusionModel(nn.Module):
                def __init__(self, m1, m2):
                    super().__init__()
                    self.m1 = m1
                    self.m2 = m2
                def forward(self, x):
                    f1 = self.m1(x)
                    f2 = self.m2(x)
                    return torch.cat([f1, f2], dim=1)
            
            model = FusionModel(convnext_part, vit_model)
        else:
            raise ValueError(f"Unknown backbone: {name}")
            
        return model, config.feature_dim

    @staticmethod
    def list_available() -> list[str]:
        return list(BACKBONE_REGISTRY.keys())

    @staticmethod
    def get_config(name: str) -> BackboneConfig:
        if name not in BACKBONE_REGISTRY:
            raise ValueError(f"Unknown backbone: {name}")
        return BACKBONE_REGISTRY[name]

    @staticmethod
    def get_transforms(name: str, is_training: bool = False):
        if not HAS_TORCH:
            raise RuntimeError("PyTorch is not available.")
        
        config = BackboneFactory.get_config(name)
        size = config.input_size
        
        if is_training:
            return T.Compose([
                T.Resize((size + 8, size + 8)),
                T.RandomCrop(size),
                T.RandomHorizontalFlip(),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
        else:
            return T.Compose([
                T.Resize((size + 8, size + 8)),
                T.CenterCrop(size),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
