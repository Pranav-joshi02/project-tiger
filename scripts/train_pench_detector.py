import argparse
import logging
import shutil
from pathlib import Path
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Fine-tune YOLOv8 on Pench species dataset.")
    parser.add_argument("--epochs", type=int, default=100, help="Number of epochs to train")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--lr0", type=float, default=0.001, help="Initial learning rate")
    parser.add_argument("--lrf", type=float, default=0.01, help="Final learning rate factor")
    parser.add_argument("--freeze", type=int, default=10, help="Number of layers to freeze")
    parser.add_argument("--patience", type=int, default=20, help="Early stopping patience")
    parser.add_argument("--save-period", type=int, default=10, help="Save period")
    parser.add_argument("--project", type=str, default="models/checkpoints", help="Project directory")
    parser.add_argument("--name", type=str, default="pench-species", help="Experiment name")
    parser.add_argument("--data", type=str, default="datasets/pench_species.yaml", help="Path to data config")
    parser.add_argument("--weights", type=str, default="yolov8n.pt", help="Path to pre-trained weights")
    
    args = parser.parse_args()
    
    logger.info(f"Loading pre-trained model: {args.weights}")
    model = YOLO(args.weights)
    
    logger.info("Starting fine-tuning...")
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        lr0=args.lr0,
        lrf=args.lrf,
        freeze=args.freeze,
        augment=True,
        patience=args.patience,
        save_period=args.save_period,
        project=args.project,
        name=args.name,
        exist_ok=True
    )
    
    logger.info("Training completed.")
    
    # Copy best weights
    best_weights = Path(args.project) / args.name / "weights" / "best.pt"
    final_weights = Path(args.project) / "pench-species-detector.pt"
    
    if best_weights.exists():
        final_weights.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(best_weights, final_weights)
        logger.info(f"Copied best weights to {final_weights}")
    else:
        logger.warning(f"Best weights not found at {best_weights}")
        
    # Print metrics
    logger.info("Evaluation Metrics:")
    if hasattr(results, 'results_dict'):
        for k, v in results.results_dict.items():
            logger.info(f"  {k}: {v}")

if __name__ == '__main__':
    main()
