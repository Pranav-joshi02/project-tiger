"""Camera event model for temporal aggregation of burst sequences.

Groups camera-trap burst images (5-20 frames within ~60 seconds) into
single events with aggregated embeddings, reducing noise from individual
blurry or partially-occluded frames.
"""
import uuid
from datetime import datetime

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class CameraEvent(Base):
    __tablename__ = "camera_events"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    station_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("stations.id"), nullable=True, index=True)
    run_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("runs.id"), nullable=True)
    encounter_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("encounters.id"), nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    frame_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)

    # Aggregated embeddings (quality-weighted mean of frame embeddings)
    aggregated_embedding = mapped_column(Vector(512), nullable=True)
    aggregated_head_embedding = mapped_column(Vector(128), nullable=True)
    aggregated_flank_embedding = mapped_column(Vector(256), nullable=True)
    aggregated_hind_embedding = mapped_column(Vector(128), nullable=True)

    # Best frame tracking
    best_frame_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("images.id"), nullable=True)
    best_frame_quality: Mapped[float | None] = mapped_column(sa.Float, nullable=True)

    # Aggregation metadata
    aggregation_strategy: Mapped[str] = mapped_column(sa.String(30), nullable=False, default="quality_weighted")
    aggregation_confidence: Mapped[float | None] = mapped_column(sa.Float, nullable=True)

    # Identity linkage
    tiger_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("tigers.id"), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
