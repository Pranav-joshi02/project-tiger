"""Temporal aggregation of camera-trap burst sequences.

Camera traps typically capture 5-20 frames per trigger event. Instead of
treating each frame independently, this module aggregates embeddings from
a burst into a single, more robust track embedding.

Strategies:
- Quality-weighted mean: E_event = Σ(w_i · E_i) / ||Σ(w_i · E_i)||₂
- Attention-weighted: Learn attention weights over frames
- Best-frame selection: Use highest quality frame only
"""

import numpy as np
from enum import Enum
from dataclasses import dataclass

class AggregationStrategy(Enum):
    QUALITY_WEIGHTED = "QUALITY_WEIGHTED"
    ATTENTION = "ATTENTION"
    BEST_FRAME = "BEST_FRAME"
    MEDIAN = "MEDIAN"

@dataclass
class FrameEmbedding:
    embedding: list[float]
    quality_score: float
    timestamp: str | None = None
    frame_index: int = 0

@dataclass
class TrackEmbedding:
    aggregated_embedding: list[float]
    strategy: str
    frame_count: int
    quality_scores: list[float]
    best_frame_index: int
    aggregation_confidence: float

class CameraEventAggregator:
    def __init__(self, strategy: AggregationStrategy = AggregationStrategy.QUALITY_WEIGHTED, min_quality: float = 0.1):
        self.strategy = strategy
        self.min_quality = min_quality

    def filter_low_quality(self, frames: list[FrameEmbedding]) -> list[FrameEmbedding]:
        return [f for f in frames if f.quality_score >= self.min_quality]

    def aggregate(self, frame_embeddings: list[FrameEmbedding]) -> TrackEmbedding:
        filtered_frames = self.filter_low_quality(frame_embeddings)
        if not filtered_frames:
            filtered_frames = frame_embeddings
            if not filtered_frames:
                raise ValueError("No frames to aggregate")

        if self.strategy == AggregationStrategy.QUALITY_WEIGHTED:
            return self._quality_weighted_mean(filtered_frames)
        elif self.strategy == AggregationStrategy.ATTENTION:
            return self._attention_weighted(filtered_frames)
        elif self.strategy == AggregationStrategy.BEST_FRAME:
            return self._best_frame(filtered_frames)
        elif self.strategy == AggregationStrategy.MEDIAN:
            return self._median(filtered_frames)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

    def _quality_weighted_mean(self, frames: list[FrameEmbedding]) -> TrackEmbedding:
        vectors = np.array([f.embedding for f in frames], dtype=np.float64)
        weights = np.array([f.quality_score for f in frames], dtype=np.float64)
        
        weighted_sum = np.sum(vectors * weights[:, np.newaxis], axis=0)
        norm = np.linalg.norm(weighted_sum)
        if norm > 0:
            weighted_sum /= norm
            
        best_idx = int(np.argmax(weights))
        confidence = float(np.mean(weights))
        
        return TrackEmbedding(
            aggregated_embedding=weighted_sum.tolist(),
            strategy=AggregationStrategy.QUALITY_WEIGHTED.value,
            frame_count=len(frames),
            quality_scores=weights.tolist(),
            best_frame_index=frames[best_idx].frame_index,
            aggregation_confidence=confidence
        )

    def _attention_weighted(self, frames: list[FrameEmbedding]) -> TrackEmbedding:
        vectors = np.array([f.embedding for f in frames], dtype=np.float64)
        weights = np.array([f.quality_score for f in frames], dtype=np.float64)
        
        exp_w = np.exp(weights - np.max(weights))
        attention = exp_w / np.sum(exp_w)
        
        weighted_sum = np.sum(vectors * attention[:, np.newaxis], axis=0)
        norm = np.linalg.norm(weighted_sum)
        if norm > 0:
            weighted_sum /= norm
            
        best_idx = int(np.argmax(attention))
        confidence = float(np.mean(weights))
        
        return TrackEmbedding(
            aggregated_embedding=weighted_sum.tolist(),
            strategy=AggregationStrategy.ATTENTION.value,
            frame_count=len(frames),
            quality_scores=weights.tolist(),
            best_frame_index=frames[best_idx].frame_index,
            aggregation_confidence=confidence
        )

    def _best_frame(self, frames: list[FrameEmbedding]) -> TrackEmbedding:
        weights = [f.quality_score for f in frames]
        best_idx = int(np.argmax(weights))
        
        return TrackEmbedding(
            aggregated_embedding=frames[best_idx].embedding,
            strategy=AggregationStrategy.BEST_FRAME.value,
            frame_count=len(frames),
            quality_scores=weights,
            best_frame_index=frames[best_idx].frame_index,
            aggregation_confidence=frames[best_idx].quality_score
        )

    def _median(self, frames: list[FrameEmbedding]) -> TrackEmbedding:
        vectors = np.array([f.embedding for f in frames], dtype=np.float64)
        median_vec = np.median(vectors, axis=0)
        
        norm = np.linalg.norm(median_vec)
        if norm > 0:
            median_vec /= norm
            
        weights = [f.quality_score for f in frames]
        best_idx = int(np.argmax(weights))
        
        return TrackEmbedding(
            aggregated_embedding=median_vec.tolist(),
            strategy=AggregationStrategy.MEDIAN.value,
            frame_count=len(frames),
            quality_scores=weights,
            best_frame_index=frames[best_idx].frame_index,
            aggregation_confidence=float(np.median(weights))
        )
