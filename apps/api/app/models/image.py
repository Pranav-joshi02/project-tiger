"""Camera-trap image model with triage state tracking."""
import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ImageState(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    QUARANTINED = "QUARANTINED"
    DUPLICATE = "DUPLICATE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    RESTORED = "RESTORED"
    REJECTED = "REJECTED"


class Image(Base):
    __tablename__ = "images"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("runs.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    sha256: Mapped[str] = mapped_column(sa.String(64), nullable=False, index=True)
    size_bytes: Mapped[int] = mapped_column(sa.BigInteger, nullable=False)
    storage_uri: Mapped[str | None] = mapped_column(sa.String(1024), nullable=True)
    quarantine_uri: Mapped[str | None] = mapped_column(sa.String(1024), nullable=True)
    state: Mapped[ImageState] = mapped_column(sa.Enum(ImageState, native_enum=False), default=ImageState.PENDING)
    triage_confidence: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    triage_category: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    model_version: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    exif_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    width: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationships
    run: Mapped["Run"] = relationship(back_populates="images")
    detections: Mapped[list["Detection"]] = relationship(back_populates="image", cascade="all, delete-orphan")
