"""Processing run model — tracks a batch of camera-trap images through the pipeline."""
import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class RunStatus(str, enum.Enum):
    PENDING = "PENDING"
    INGESTING = "INGESTING"
    TRIAGING = "TRIAGING"
    DETECTING = "DETECTING"
    EMBEDDING = "EMBEDDING"
    IDENTIFYING = "IDENTIFYING"
    ANALYZING = "ANALYZING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    status: Mapped[RunStatus] = mapped_column(sa.Enum(RunStatus, native_enum=False), default=RunStatus.PENDING)
    source_directory: Mapped[str] = mapped_column(sa.String(1024), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    started_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # Aggregate stats (updated as pipeline progresses)
    total_images: Mapped[int] = mapped_column(sa.Integer, default=0)
    duplicate_images: Mapped[int] = mapped_column(sa.Integer, default=0)
    quarantined_images: Mapped[int] = mapped_column(sa.Integer, default=0)
    retained_images: Mapped[int] = mapped_column(sa.Integer, default=0)
    tiger_detections: Mapped[int] = mapped_column(sa.Integer, default=0)
    new_tigers: Mapped[int] = mapped_column(sa.Integer, default=0)
    auto_matched: Mapped[int] = mapped_column(sa.Integer, default=0)
    for_review: Mapped[int] = mapped_column(sa.Integer, default=0)
    quarantined_bytes: Mapped[int] = mapped_column(sa.BigInteger, default=0)
    processing_duration_seconds: Mapped[float | None] = mapped_column(sa.Float, nullable=True)

    # Relationships
    creator: Mapped["User | None"] = relationship(back_populates="runs")
    images: Mapped[list["Image"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    encounters: Mapped[list["Encounter"]] = relationship(back_populates="run", cascade="all, delete-orphan")
