"""Tiger observation linking a tiger to an image at a station."""
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    tiger_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("tigers.id"), nullable=False, index=True)
    station_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("stations.id"), nullable=False, index=True)
    image_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("images.id"), nullable=True)
    encounter_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("encounters.id"), nullable=True)
    detection_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("detections.id"), nullable=True)
    location = mapped_column(sa.JSON, nullable=True)
    identity_confidence: Mapped[float] = mapped_column(sa.Float, nullable=False)
    identity_method: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="AUTO")
    flank_side: Mapped[str | None] = mapped_column(sa.String(10), nullable=True)
    captured_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationships
    tiger: Mapped["Tiger"] = relationship(back_populates="observations")
    station: Mapped["Station"] = relationship(back_populates="observations")
    encounter: Mapped["Encounter | None"] = relationship(back_populates="observations")
