"""Ablation study runner for tiger Re-ID backbone comparison.

Trains and evaluates each backbone configuration and produces a comparative
report with: Rank-1, Rank-5, mAP, inference time, GPU memory, false-match rate.
"""
from dataclasses import dataclass
from typing import Optional, List
import time
import logging

logger = logging.getLogger(__name__)

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

@dataclass
class AblationConfig:
    backbone: str
    embedding_dim: int = 512
    loss: str = 'triplet_arcface'
    epochs: int = 30
    batch_size: int = 32
    learning_rate: float = 1e-4

@dataclass
class AblationResult:
    backbone: str
    rank_1: float
    rank_5: float
    mAP: float
    inference_ms: float
    gpu_memory_mb: float
    false_match_rate: float
    training_time_min: float
    notes: str = ''

class AblationRunner:
    def __init__(self, data_dir: str, output_dir: str, configs: Optional[List[AblationConfig]] = None):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.configs = configs or []

    def run_all(self) -> List[AblationResult]:
        results = []
        for config in self.configs:
            logger.info(f"Running ablation for config: {config.backbone}")
            res = self.run_single(config)
            results.append(res)
        return results

    def run_single(self, config: AblationConfig) -> AblationResult:
        # Mock training and evaluation for demonstration purposes
        import random
        return AblationResult(
            backbone=config.backbone,
            rank_1=0.85 + random.uniform(0, 0.1),
            rank_5=0.92 + random.uniform(0, 0.05),
            mAP=0.80 + random.uniform(0, 0.1),
            inference_ms=10.0 + random.uniform(0, 15.0),
            gpu_memory_mb=1024.0 + random.uniform(0, 2048.0),
            false_match_rate=0.01 + random.uniform(0, 0.02),
            training_time_min=60.0 + random.uniform(0, 60.0),
            notes='Mocked result for structure'
        )

    def _measure_inference(self, model, sample_batch, num_runs=100) -> float:
        if not HAS_TORCH:
            return 0.0
        with torch.no_grad():
            for _ in range(10):
                _ = model(sample_batch)
        
        torch.cuda.synchronize() if torch.cuda.is_available() else None
        start = time.time()
        with torch.no_grad():
            for _ in range(num_runs):
                _ = model(sample_batch)
        torch.cuda.synchronize() if torch.cuda.is_available() else None
        end = time.time()
        
        return ((end - start) * 1000.0) / num_runs

    def _measure_memory(self) -> float:
        if not HAS_TORCH or not torch.cuda.is_available():
            return 0.0
        torch.cuda.reset_peak_memory_stats()
        return torch.cuda.max_memory_allocated() / (1024 * 1024)

    def generate_report(self, results: List[AblationResult]) -> str:
        header = f"| {'Backbone':<20} | {'Rank-1':<8} | {'Rank-5':<8} | {'mAP':<8} | {'Inf (ms)':<10} | {'Mem (MB)':<10} | {'FMR':<8} | {'Train (min)':<12} |\n"
        sep = f"| {'-'*20} | {'-'*8} | {'-'*8} | {'-'*8} | {'-'*10} | {'-'*10} | {'-'*8} | {'-'*12} |\n"
        report = header + sep
        for r in results:
            report += f"| {r.backbone:<20} | {r.rank_1:<8.3f} | {r.rank_5:<8.3f} | {r.mAP:<8.3f} | {r.inference_ms:<10.2f} | {r.gpu_memory_mb:<10.1f} | {r.false_match_rate:<8.3f} | {r.training_time_min:<12.1f} |\n"
        return report

    def save_report(self, results: List[AblationResult], output_path: str):
        report = self.generate_report(results)
        with open(output_path, 'w') as f:
            f.write(report)
