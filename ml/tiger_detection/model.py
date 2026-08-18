from pathlib import Path
def load(weights:Path):
    from ultralytics import YOLO
    return YOLO(str(weights))
