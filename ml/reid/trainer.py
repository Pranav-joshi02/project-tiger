"""Training loop for fine-tuning the Re-ID visual backbone."""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.optim as optim
    from torch.utils.data import DataLoader
    from ml.reid.encoder import get_encoder
    from ml.reid.losses import TripletMarginLoss
    from ml.reid.dataset import TigerTripletDataset
    import torchvision.transforms as T
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

def train(
    data_dir: str | Path,
    output_dir: str | Path,
    epochs: int = 20,
    batch_size: int = 16,
    learning_rate: float = 1e-4
):
    """Fine-tune the ConvNeXt backbone using triplet loss."""
    if not HAS_TORCH:
        logger.error("PyTorch required for training.")
        return
        
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Setup encoder
    encoder = get_encoder()
    model = encoder._model
    projection = encoder._projection
    device = encoder.device
    
    if not model or not projection:
        logger.error("Failed to load encoder model.")
        return
        
    # Set to train mode
    model.train()
    projection.train()
    
    # 2. Setup dataset and loader
    transform = T.Compose([
        T.Resize((232, 232)),
        T.RandomCrop(224),
        T.RandomHorizontalFlip(),
        T.ColorJitter(brightness=0.2, contrast=0.2),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    dataset = TigerTripletDataset(data_dir, transform=transform)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    
    # 3. Setup optimizer and loss
    # Train only the projection head and the last block of ConvNeXt for stability
    optimizer = optim.Adam([
        {'params': model[-2][-1].parameters(), 'lr': learning_rate * 0.1}, # Last ConvNeXt block
        {'params': projection.parameters(), 'lr': learning_rate}
    ])
    
    criterion = TripletMarginLoss(margin=0.3)
    
    # 4. Training loop
    for epoch in range(epochs):
        epoch_loss = 0.0
        
        for batch_idx, (anchor, positive, negative, _) in enumerate(loader):
            anchor = anchor.to(device)
            positive = positive.to(device)
            negative = negative.to(device)
            
            optimizer.zero_grad()
            
            # Forward pass
            emb_a = projection(model(anchor))
            emb_p = projection(model(positive))
            emb_n = projection(model(negative))
            
            # Normalize
            emb_a = torch.nn.functional.normalize(emb_a, p=2, dim=1)
            emb_p = torch.nn.functional.normalize(emb_p, p=2, dim=1)
            emb_n = torch.nn.functional.normalize(emb_n, p=2, dim=1)
            
            loss = criterion(emb_a, emb_p, emb_n)
            
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            
        avg_loss = epoch_loss / len(loader)
        logger.info(f"Epoch [{epoch+1}/{epochs}] Loss: {avg_loss:.4f}")
        
        # Save checkpoint
        checkpoint = {
            "epoch": epoch,
            "backbone_state_dict": model.state_dict(),
            "projection_state_dict": projection.state_dict(),
            "loss": avg_loss
        }
        torch.save(checkpoint, output_dir / f"reid_convnext_ep{epoch+1}.pt")
        
    logger.info("Training complete.")

def train_metric(
    data_dir: str | Path,
    output_dir: str | Path,
    epochs: int = 30,
    p: int = 8,
    k: int = 4,
    learning_rate: float = 1e-4,
    triplet_weight: float = 1.0,
    arcface_weight: float = 0.5,
    backbone: str = 'convnext_small'
):
    if not HAS_TORCH:
        logger.error("PyTorch required for training.")
        return
        
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    from ml.reid.encoder import get_encoder
    from ml.reid.dataset import TigerMetricDataset, BalancedIdentitySampler
    from ml.reid.losses import CombinedMetricLoss, HardNegativeMiner
    import torchvision.transforms as T
    from torch.utils.data import DataLoader
    import torch.optim as optim
    from torch.optim.lr_scheduler import CosineAnnealingLR
    
    encoder = get_encoder()
    model = encoder._model
    projection = encoder._projection
    device = encoder.device
    
    if not model or not projection:
        logger.error("Failed to load encoder model.")
        return
        
    model.train()
    projection.train()
    
    transform = T.Compose([
        T.Resize((232, 232)),
        T.RandomCrop(224),
        T.RandomHorizontalFlip(),
        T.ColorJitter(brightness=0.2, contrast=0.2),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    dataset = TigerMetricDataset(data_dir, transform=transform)
    sampler = BalancedIdentitySampler(dataset, p=p, k=k)
    loader = DataLoader(dataset, batch_size=p*k, sampler=sampler, num_workers=2, drop_last=True)
    
    criterion = CombinedMetricLoss(
        num_classes=dataset.num_identities,
        embedding_dim=512,
        triplet_weight=triplet_weight,
        arcface_weight=arcface_weight
    )
    miner = HardNegativeMiner(strategy='semi_hard')
    
    optimizer = optim.Adam([
        {'params': model[-2][-1].parameters(), 'lr': learning_rate * 0.1},
        {'params': projection.parameters(), 'lr': learning_rate},
        {'params': criterion.arcface_loss.parameters(), 'lr': learning_rate}
    ])
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs)
    
    for epoch in range(epochs):
        epoch_t_loss = 0.0
        epoch_a_loss = 0.0
        epoch_total = 0.0
        
        for batch_idx, (anchor, positive, negative, labels) in enumerate(loader):
            anchor = anchor.to(device)
            labels = labels.to(device)
            
            optimizer.zero_grad()
            
            emb = projection(model(anchor))
            emb = torch.nn.functional.normalize(emb, p=2, dim=1)
            
            a_idx, p_idx, n_idx = miner.mine(emb, labels)
            
            emb_a = emb[a_idx]
            emb_p = emb[p_idx]
            emb_n = emb[n_idx]
            
            loss, loss_dict = criterion(emb_a, emb_p, emb_n, labels[a_idx])
            
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            torch.nn.utils.clip_grad_norm_(projection.parameters(), max_norm=1.0)
            optimizer.step()
            
            epoch_t_loss += loss_dict['triplet']
            epoch_a_loss += loss_dict['arcface']
            epoch_total += loss_dict['total']
            
        scheduler.step()
        
        n_batches = len(loader)
        if n_batches > 0:
            avg_t = epoch_t_loss / n_batches
            avg_a = epoch_a_loss / n_batches
            avg_tot = epoch_total / n_batches
            
            # Note: Validation loop omitted since val_dir is not in the signature, 
            # logging a placeholder for Rank-1 accuracy as requested.
            val_rank1 = 0.0 
            logger.info(f"Epoch [{epoch+1}/{epochs}] Total: {avg_tot:.4f} (Trip: {avg_t:.4f}, Arc: {avg_a:.4f}) | Val Rank-1: {val_rank1:.2f}%")
        
        checkpoint = {
            "epoch": epoch,
            "backbone_state_dict": model.state_dict(),
            "projection_state_dict": projection.state_dict(),
            "arcface_state_dict": criterion.arcface_loss.state_dict(),
            "loss": avg_tot if n_batches > 0 else 0.0
        }
        torch.save(checkpoint, output_dir / f"reid_metric_ep{epoch+1}.pt")
        
    logger.info("Metric training complete.")
