"""Tiger visual embedding for re-identification via pgvector.

Supports multi-part body feature embeddings (global, head, flank, hind)
alongside the primary fused 512-D vector used for pgvector search.
"""
import uuid
from datetime import datetime

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    flank_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("flanks.id"), nullable=True, index=True)
    tiger_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("tigers.id"), nullable=True, index=True)
    vector = mapped_column(Vector(512), nullable=False)
    model_version: Mapped[str] = mapped_column(sa.String(100), nullable=False, default="convnext-small-v1")
    side: Mapped[str | None] = mapped_column(sa.String(10), nullable=True)
    quality_weight: Mapped[float] = mapped_column(sa.Float, nullable=False, default=1.0)
    is_prototype: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    confirmed: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Multi-part body feature embeddings (Items #2, #3, #4)
    head_embedding = mapped_column(Vector(128), nullable=True)
    flank_embedding = mapped_column(Vector(256), nullable=True)
    hind_embedding = mapped_column(Vector(128), nullable=True)
    visible_parts = mapped_column(sa.ARRAY(sa.String(20)), nullable=True)
    pose_confidence: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    part_type: Mapped[str | None] = mapped_column(sa.String(20), nullable=True, default="global")
    stripe_quality: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    observation_id: Mapped[uuid.UUID | None] = mapped_column(sa.Uuid, nullable=True)

    # Relationships
    flank: Mapped["Flank | None"] = relationship(back_populates="embeddings", foreign_keys=[flank_id])
    tiger: Mapped["Tiger | None"] = relationship(back_populates="embeddings", foreign_keys=[tiger_id])
