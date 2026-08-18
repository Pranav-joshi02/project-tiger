"""Strict negative constraint / rejected claims model for Re-ID.

Ensures that if an expert reviewer or algorithm rejects a proposed identity match,
that individual tiger is strictly blocked from ever matching that observation/flank/image
in all future Re-ID passes, candidate searches, and continuous learning updates.
"""
import uuid
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class NegativeConstraint(Base):
    """Stores hard 'cannot-link' negative pair constraints."""
    __tablename__ = "negative_constraints"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    tiger_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("tigers.id", ondelete="CASCADE"), nullable=False, index=True)
    image_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("images.id", ondelete="SET NULL"), nullable=True, index=True)
    flank_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("flanks.id", ondelete="SET NULL"), nullable=True, index=True)
    detection_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("detections.id", ondelete="SET NULL"), nullable=True)
    review_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("reviews.id", ondelete="SET NULL"), nullable=True, index=True)
    image_sha256: Mapped[str | None] = mapped_column(sa.String(64), nullable=True, index=True)
    reason: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    reviewer_note: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), index=True)
