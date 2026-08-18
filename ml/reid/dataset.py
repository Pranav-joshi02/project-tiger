"""Dataset loaders for metric learning."""
import logging
from pathlib import Path
import random

logger = logging.getLogger(__name__)

try:
    from torch.utils.data import Dataset
    from PIL import Image
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    Dataset = object # Stub

class TigerTripletDataset(Dataset):
    """Samples Anchor, Positive, Negative triplets for training."""
    
    def __init__(self, data_dir: str | Path, transform=None):
        if not HAS_TORCH:
            raise ImportError("PyTorch/Torchvision required for dataset")
            
        self.data_dir = Path(data_dir)
        self.transform = transform
        
        # Expecting directory structure: data_dir / tiger_id / image.jpg
        self.identities = [d for d in self.data_dir.iterdir() if d.is_dir()]
        self.images = []
        self.id_to_images = {}
        
        for idx, tiger_dir in enumerate(self.identities):
            imgs = list(tiger_dir.glob("*.jpg")) + list(tiger_dir.glob("*.png"))
            if len(imgs) >= 2: # Need at least 2 images for an anchor-positive pair
                self.id_to_images[idx] = imgs
                for img in imgs:
                    self.images.append((img, idx))
                    
        logger.info(f"Loaded {len(self.images)} images across {len(self.id_to_images)} identities.")

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        anchor_path, label = self.images[idx]
        
        # Sample positive
        positive_path = random.choice([p for p in self.id_to_images[label] if p != anchor_path])
        
        # Sample negative
        negative_label = random.choice([l for l in self.id_to_images.keys() if l != label])
        negative_path = random.choice(self.id_to_images[negative_label])
        
        anchor_img = Image.open(anchor_path).convert("RGB")
        positive_img = Image.open(positive_path).convert("RGB")
        negative_img = Image.open(negative_path).convert("RGB")
        
        if self.transform:
            anchor_img = self.transform(anchor_img)
            positive_img = self.transform(positive_img)
            negative_img = self.transform(negative_img)
            
        return anchor_img, positive_img, negative_img, label

from collections import defaultdict

class TigerMetricDataset(Dataset):
    """Supports both triplet sampling AND classification labels."""
    
    def __init__(self, data_dir: str | Path, transform=None, mode='triplet_classification'):
        if not HAS_TORCH:
            raise ImportError("PyTorch/Torchvision required for dataset")
            
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.mode = mode
        
        self.identities = [d for d in self.data_dir.iterdir() if d.is_dir()]
        self.images = []
        self.id_to_images = {}
        
        valid_idx = 0
        for tiger_dir in self.identities:
            imgs = list(tiger_dir.glob("*.jpg")) + list(tiger_dir.glob("*.png"))
            if len(imgs) >= 2:
                self.id_to_images[valid_idx] = imgs
                for img in imgs:
                    self.images.append((img, valid_idx))
                valid_idx += 1
                
        logger.info(f"Loaded {len(self.images)} images across {len(self.id_to_images)} identities.")

    @property
    def num_identities(self):
        return len(self.id_to_images)

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        anchor_path, label = self.images[idx]
        
        positive_path = random.choice([p for p in self.id_to_images[label] if p != anchor_path])
        negative_label = random.choice([l for l in self.id_to_images.keys() if l != label])
        negative_path = random.choice(self.id_to_images[negative_label])
        
        anchor_img = Image.open(anchor_path).convert("RGB")
        positive_img = Image.open(positive_path).convert("RGB")
        negative_img = Image.open(negative_path).convert("RGB")
        
        if self.transform:
            anchor_img = self.transform(anchor_img)
            positive_img = self.transform(positive_img)
            negative_img = self.transform(negative_img)
            
        return anchor_img, positive_img, negative_img, label

try:
    from torch.utils.data.sampler import Sampler
except ImportError:
    Sampler = object

class BalancedIdentitySampler(Sampler):
    """PK sampling strategy"""
    def __init__(self, dataset: TigerMetricDataset, p: int = 8, k: int = 4):
        self.dataset = dataset
        self.p = p
        self.k = k
        self.id_to_indices = defaultdict(list)
        for idx, (_, label) in enumerate(dataset.images):
            self.id_to_indices[label].append(idx)
            
        self.valid_identities = list(self.id_to_indices.keys())
        
    def __iter__(self):
        batch_indices = []
        identities = list(self.valid_identities)
        random.shuffle(identities)
        
        for i in range(0, len(identities), self.p):
            batch_ids = identities[i:i+self.p]
            if len(batch_ids) < self.p:
                continue
                
            for identity in batch_ids:
                indices = self.id_to_indices[identity]
                if len(indices) >= self.k:
                    sampled = random.sample(indices, self.k)
                else:
                    sampled = random.choices(indices, k=self.k)
                batch_indices.extend(sampled)
                
            yield from batch_indices
            batch_indices = []

    def __len__(self):
        return (len(self.valid_identities) // self.p) * self.p * self.k

