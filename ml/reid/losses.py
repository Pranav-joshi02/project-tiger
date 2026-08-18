"""Metric learning loss functions for tiger Re-ID."""
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

class TripletMarginLoss(Any):
    """Standard triplet margin loss for metric learning."""
    
    def __init__(self, margin: float = 0.3):
        if not HAS_TORCH:
            raise ImportError("PyTorch is required for metric learning")
        super().__init__()
        self.margin = margin
        self.loss_fn = nn.TripletMarginLoss(margin=margin, p=2)
        
    def __call__(self, anchor: "torch.Tensor", positive: "torch.Tensor", negative: "torch.Tensor") -> "torch.Tensor":
        return self.loss_fn(anchor, positive, negative)

class ContrastiveLoss(Any):
    """Contrastive loss for pair-based learning."""
    
    def __init__(self, margin: float = 1.0):
        if not HAS_TORCH:
            raise ImportError("PyTorch is required for metric learning")
        super().__init__()
        self.margin = margin
        
    def __call__(self, emb1: "torch.Tensor", emb2: "torch.Tensor", label: "torch.Tensor") -> "torch.Tensor":
        """
        label: 1 for same identity, 0 for different
        """
        distance = F.pairwise_distance(emb1, emb2, p=2)
        loss_contrastive = torch.mean((label) * torch.pow(distance, 2) +
                                      (1 - label) * torch.pow(torch.clamp(self.margin - distance, min=0.0), 2))
        return loss_contrastive

class ArcFaceLoss(nn.Module):
    def __init__(self, num_classes: int, embedding_dim: int = 512, s: float = 30.0, m: float = 0.50):
        super().__init__()
        self.num_classes = num_classes
        self.s = s
        self.m = m
        self.W = nn.Parameter(torch.empty(num_classes, embedding_dim))
        nn.init.xavier_uniform_(self.W)

    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        emb_norm = F.normalize(embeddings, p=2, dim=1)
        W_norm = F.normalize(self.W, p=2, dim=1)
        cosine = F.linear(emb_norm, W_norm)
        
        # Add margin
        theta = torch.acos(torch.clamp(cosine, -1.0 + 1e-7, 1.0 - 1e-7))
        target_logits = torch.cos(theta + self.m)
        
        # One hot encode
        one_hot = torch.zeros_like(cosine)
        one_hot.scatter_(1, labels.view(-1, 1).long(), 1)
        
        logits = torch.where(one_hot == 1, target_logits, cosine)
        logits = logits * self.s
        
        return F.cross_entropy(logits, labels)

class CombinedMetricLoss:
    def __init__(self, num_classes: int, embedding_dim=512, triplet_weight=1.0, arcface_weight=0.5, triplet_margin=0.3, arcface_s=30.0, arcface_m=0.50):
        self.triplet_weight = triplet_weight
        self.arcface_weight = arcface_weight
        self.triplet_loss = nn.TripletMarginLoss(margin=triplet_margin, p=2)
        self.arcface_loss = ArcFaceLoss(num_classes=num_classes, embedding_dim=embedding_dim, s=arcface_s, m=arcface_m)
        
    def __call__(self, anchor, positive, negative, labels) -> tuple[torch.Tensor, dict]:
        t_loss = self.triplet_loss(anchor, positive, negative)
        a_loss = self.arcface_loss(anchor, labels)
        
        total = self.triplet_weight * t_loss + self.arcface_weight * a_loss
        
        return total, {
            "triplet": t_loss.item(),
            "arcface": a_loss.item(),
            "total": total.item()
        }

class HardNegativeMiner:
    def __init__(self, strategy: str = 'semi_hard'):
        self.strategy = strategy
        
    def mine(self, embeddings: torch.Tensor, labels: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        dist_mat = self._pairwise_distances(embeddings)
        
        if self.strategy == 'hard':
            return self._mine_batch_hard(dist_mat, labels)
        elif self.strategy == 'semi_hard':
            return self._mine_semi_hard(dist_mat, labels)
        elif self.strategy == 'batch_all':
            return self._mine_semi_hard(dist_mat, labels)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
            
    def _mine_batch_hard(self, dist_mat, labels):
        n = dist_mat.size(0)
        is_pos = labels.expand(n, n).eq(labels.expand(n, n).t())
        is_neg = labels.expand(n, n).ne(labels.expand(n, n).t())
        
        dist_ap, relative_p_inds = torch.max(dist_mat - (~is_pos).float() * 1e5, dim=1)
        dist_an, relative_n_inds = torch.min(dist_mat + (~is_neg).float() * 1e5, dim=1)
        
        anchor_indices = torch.arange(n, device=dist_mat.device)
        return anchor_indices, relative_p_inds, relative_n_inds

    def _mine_semi_hard(self, dist_mat, labels):
        return self._mine_batch_hard(dist_mat, labels)

    def _pairwise_distances(self, embeddings):
        dot_product = torch.mm(embeddings, embeddings.t())
        square_norm = torch.diag(dot_product)
        distances = square_norm.unsqueeze(0) - 2.0 * dot_product + square_norm.unsqueeze(1)
        distances = torch.clamp(distances, min=0.0)
        return torch.sqrt(distances + 1e-16)
