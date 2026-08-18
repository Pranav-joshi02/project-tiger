"""Encounter grouping model."""
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY

from app.db.session import Base

class Encounter(Base):
    __tablename__ = "encounters"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("runs.id"), nullable=False, index=True)
    station_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("stations.id"), nullable=False, index=True)
    best_image_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("images.id"), nullable=True)
    
    started_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    image_count: Mapped[int] = mapped_column(sa.Integer, default=1)
    
    # Store tigers identified in this encounter
    tiger_ids: Mapped[list[uuid.UUID] | None] = mapped_column(ARRAY(sa.Uuid), nullable=True)

    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationships
    run: Mapped["Run"] = relationship(back_populates="encounters")
    station: Mapped["Station"] = relationship(back_populates="encounters")
    best_image: Mapped["Image"] = relationship()
    observations: Mapped[list["Observation"]] = relationship(back_populates="encounter")
