"""Human-in-the-loop identity review model."""
import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ReviewState(str, enum.Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    DECIDED = "DECIDED"
    EXPIRED = "EXPIRED"


class ReviewDecisionType(str, enum.Enum):
    ACCEPT_CANDIDATE = "ACCEPT_CANDIDATE"
    ENROLL_NEW = "ENROLL_NEW"
    REJECT = "REJECT"


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    image_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("images.id"), nullable=True)
    detection_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("detections.id"), nullable=True)
    flank_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("flanks.id"), nullable=True)
    suggested_tiger_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("tigers.id"), nullable=True)
    assigned_tiger_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("tigers.id"), nullable=True)
    state: Mapped[ReviewState] = mapped_column(sa.Enum(ReviewState, native_enum=False), default=ReviewState.PENDING, index=True)
    decision: Mapped[ReviewDecisionType | None] = mapped_column(sa.Enum(ReviewDecisionType, native_enum=False), nullable=True)
    similarity_score: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    candidates: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # [{tiger_id, similarity, ...}]
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("users.id"), nullable=True)
    reviewer_note: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), index=True)

    # Relationships
    reviewer: Mapped["User | None"] = relationship(back_populates="reviews")
