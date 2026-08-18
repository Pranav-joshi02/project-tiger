"""Object detection result from tiger/species detection."""
import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class DetectionCategory(str, enum.Enum):
    TIGER = "TIGER"
    SPOTTED_DEER = "SPOTTED_DEER"
    SLOTH_BEAR = "SLOTH_BEAR"
    ANIMAL = "ANIMAL"
    PERSON = "PERSON"
    VEHICLE = "VEHICLE"
    UNKNOWN = "UNKNOWN"


class Detection(Base):
    __tablename__ = "detections"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    image_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("images.id"), nullable=False, index=True)
    category: Mapped[DetectionCategory] = mapped_column(sa.Enum(DetectionCategory, native_enum=False), nullable=False)
    confidence: Mapped[float] = mapped_column(sa.Float, nullable=False)
    bbox: Mapped[list[float]] = mapped_column(ARRAY(sa.Float), nullable=False)  # [x1, y1, x2, y2]
    crop_uri: Mapped[str | None] = mapped_column(sa.String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationships
    image: Mapped["Image"] = relationship(back_populates="detections")
    flanks: Mapped[list["Flank"]] = relationship(back_populates="detection", cascade="all, delete-orphan")
