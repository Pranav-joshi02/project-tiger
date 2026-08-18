"""Tiger home-range estimates computed from observations."""
import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class RangeMethod(str, enum.Enum):
    MCP = "MCP"
    KDE_95 = "KDE_95"
    KDE_50 = "KDE_50"


class TigerRange(Base):
    __tablename__ = "tiger_ranges"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    tiger_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("tigers.id"), nullable=False, index=True)
    method: Mapped[RangeMethod] = mapped_column(sa.Enum(RangeMethod, native_enum=False), nullable=False)
    polygon = mapped_column(sa.JSON, nullable=True)
    area_km2: Mapped[float] = mapped_column(sa.Float, nullable=False, default=0.0)
    centroid = mapped_column(sa.JSON, nullable=True)
    observation_count: Mapped[int] = mapped_column(sa.Integer, default=0)
    period_start: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationships
    tiger: Mapped["Tiger"] = relationship(back_populates="ranges")
