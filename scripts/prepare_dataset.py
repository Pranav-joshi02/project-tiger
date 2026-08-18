import os
import argparse
import random
import shutil
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CLASS_MAP = {
    'tiger': 0,
    'spotted_deer': 1,
    'sloth_bear': 2,
    'leopard': 3,
    'other_animal': 4
}

def create_pseudo_annotation(label_path: Path, class_id: int):
    # Full image bounding box (class_id, x_center, y_center, width, height)
    with open(label_path, 'w') as f:
        f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")

def main():
    parser = argparse.ArgumentParser(description="Prepare downloaded dataset for YOLO training.")
    parser.add_argument("--input-dir", type=str, default="datasets/pench_species/images/raw", help="Directory with raw downloaded images")
    parser.add_argument("--output-dir", type=str, default="datasets/pench_species", help="Base output directory for YOLO dataset")
    parser.add_argument("--val-split", type=float, default=0.2, help="Validation set split ratio")
    parser.add_argument("--test-split", type=float, default=0.1, help="Test set split ratio")
    
    args = parser.parse_args()
    
    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir)
    
    if not in_dir.exists():
        logger.error(f"Input directory {in_dir} does not exist.")
        return
        
    splits = ['train', 'val', 'test']
    for split in splits:
        (out_dir / 'images' / split).mkdir(parents=True, exist_ok=True)
        (out_dir / 'labels' / split).mkdir(parents=True, exist_ok=True)
        
    class_distribution = {split: {k: 0 for k in CLASS_MAP.keys()} for split in splits}
    
    for species_folder in in_dir.iterdir():
        if not species_folder.is_dir():
            continue
            
        species_name = species_folder.name
        if species_name not in CLASS_MAP:
            logger.warning(f"Unknown species {species_name}, skipping.")
            continue
            
        class_id = CLASS_MAP[species_name]
        
        images = [f for f in species_folder.iterdir() if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
        random.shuffle(images)
        
        n_total = len(images)
        n_test = int(n_total * args.test_split)
        n_val = int(n_total * args.val_split)
        n_train = n_total - n_test - n_val
        
        splits_assignment = ['train'] * n_train + ['val'] * n_val + ['test'] * n_test
        random.shuffle(splits_assignment)
        
        for img_path, split in zip(images, splits_assignment):
            # Copy image
            new_img_path = out_dir / 'images' / split / img_path.name
            shutil.copy2(img_path, new_img_path)
            
            # Create pseudo-annotation
            label_name = img_path.stem + '.txt'
            label_path = out_dir / 'labels' / split / label_name
            create_pseudo_annotation(label_path, class_id)
            
            class_distribution[split][species_name] += 1
            
    logger.info("Dataset preparation complete.")
    logger.info("Class Distribution Report:")
    for split in splits:
        logger.info(f"Split: {split}")
        for species, count in class_distribution[split].items():
            logger.info(f"  {species}: {count}")

if __name__ == '__main__':
    main()
