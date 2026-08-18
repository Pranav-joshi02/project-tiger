from pathlib import Path
from .detector import load_detector
def infer(path:Path): return load_detector().evaluate(path,.30,.80)
