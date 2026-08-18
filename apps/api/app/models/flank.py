"""Tiger flank extraction for re-identification."""
import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class FlankSide(str, enum.Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    UNKNOWN = "UNKNOWN"


class Flank(Base):
    __tablename__ = "flanks"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    detection_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("detections.id"), nullable=False, index=True)
    side: Mapped[FlankSide] = mapped_column(sa.Enum(FlankSide, native_enum=False), nullable=False)
    quality_score: Mapped[float] = mapped_column(sa.Float, nullable=False, default=0.0)
    blur_score: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    exposure_score: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    occlusion_score: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    crop_uri: Mapped[str | None] = mapped_column(sa.String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationships
    detection: Mapped["Detection"] = relationship(back_populates="flanks")
    embeddings: Mapped[list["Embedding"]] = relationship(back_populates="flank", cascade="all, delete-orphan")
