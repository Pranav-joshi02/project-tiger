import torch
import torch.nn as nn
import torch.nn.functional as F

class TemporalContrastiveSSL(nn.Module):
    """
    Self-supervised contrastive learning leveraging unlabeled camera-trap bursts.
    Treats frames at t and t+dt as positive pairs, and temporal distant tracks as negatives.
    Implements NT-Xent / InfoNCE loss on temporal pairs.
    """
    def __init__(self, feature_dim: int = 512, temperature: float = 0.07):
        """
        Args:
            feature_dim (int): Dimensionality of the feature embeddings.
            temperature (float): Temperature scaling factor for NT-Xent loss.
        """
        super().__init__()
        self.feature_dim = feature_dim
        self.temperature = temperature
        
    def forward(self, features_t: torch.Tensor, features_t_plus_dt: torch.Tensor) -> torch.Tensor:
        """
        Computes the contrastive loss between two temporally adjacent feature sets.
        
        Args:
            features_t (torch.Tensor): Features at time t, shape (B, D).
            features_t_plus_dt (torch.Tensor): Features at time t+dt, shape (B, D).
            
        Returns:
            torch.Tensor: The NT-Xent loss.
        """
        batch_size = features_t.size(0)
        
        # Normalize features
        z_i = F.normalize(features_t, dim=1)
        z_j = F.normalize(features_t_plus_dt, dim=1)
        
        # Concatenate for self-similarity matrix
        representations = torch.cat([z_i, z_j], dim=0)
        
        # Compute similarity matrix
        similarity_matrix = F.cosine_similarity(representations.unsqueeze(1), representations.unsqueeze(0), dim=2)
        
        # Mask out self-similarity
        mask = torch.eye(2 * batch_size, dtype=torch.bool, device=similarity_matrix.device)
        similarity_matrix = similarity_matrix[~mask].view(2 * batch_size, -1)
        
        # Positive samples are at offset `batch_size`
        positives = torch.cat([
            torch.diag(similarity_matrix, batch_size - 1),
            torch.diag(similarity_matrix, -batch_size)
        ])
        
        # Temperature scaling
        similarity_matrix /= self.temperature
        positives /= self.temperature
        
        numerator = torch.exp(positives)
        denominator = torch.sum(torch.exp(similarity_matrix), dim=1)
        
        loss = -torch.log(numerator / denominator).mean()
        
        return loss
