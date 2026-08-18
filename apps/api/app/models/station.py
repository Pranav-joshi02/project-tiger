"""Camera station model with GPS location."""
import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class StationZone(str, enum.Enum):
    CORE = "CORE"
    BUFFER = "BUFFER"


class StationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    INACTIVE = "INACTIVE"


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(sa.String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False, default="")
    latitude: Mapped[float] = mapped_column(sa.Float, nullable=False, default=0.0)
    longitude: Mapped[float] = mapped_column(sa.Float, nullable=False, default=0.0)
    location = mapped_column(sa.JSON, nullable=True)
    zone: Mapped[StationZone] = mapped_column(sa.Enum(StationZone, native_enum=False), nullable=False)
    status: Mapped[StationStatus] = mapped_column(sa.Enum(StationStatus, native_enum=False), default=StationStatus.ACTIVE)
    reserve_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("reserves.id"), nullable=True)
    elevation_m: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    last_check: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationships
    reserve: Mapped["Reserve | None"] = relationship(back_populates="stations")
    observations: Mapped[list["Observation"]] = relationship(back_populates="station")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="station")
    encounters: Mapped[list["Encounter"]] = relationship(back_populates="station", cascade="all, delete-orphan")
