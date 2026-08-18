"""Conservation alert model for spatial and behavioral anomalies."""
import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class AlertType(str, enum.Enum):
    RANGE_SHIFT = "RANGE_SHIFT"
    NEW_TERRITORY = "NEW_TERRITORY"
    BUFFER_MOVEMENT = "BUFFER_MOVEMENT"
    EXTENDED_ABSENCE = "EXTENDED_ABSENCE"
    CAMERA_HEALTH = "CAMERA_HEALTH"
    SURVEY_ARTIFACT = "SURVEY_ARTIFACT"
    STATION_NOVELTY = "STATION_NOVELTY"


class AlertSeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AlertStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    tiger_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("tigers.id"), nullable=True, index=True)
    station_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("stations.id"), nullable=True)
    type: Mapped[AlertType] = mapped_column(sa.Enum(AlertType, native_enum=False), nullable=False)
    severity: Mapped[AlertSeverity] = mapped_column(sa.Enum(AlertSeverity, native_enum=False), nullable=False)
    status: Mapped[AlertStatus] = mapped_column(sa.Enum(AlertStatus, native_enum=False), default=AlertStatus.ACTIVE)
    title: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    summary: Mapped[str] = mapped_column(sa.Text, nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rule_version: Mapped[str] = mapped_column(sa.String(50), default="v1.0")
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("users.id"), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationships
    tiger: Mapped["Tiger | None"] = relationship(back_populates="alerts")
    station: Mapped["Station | None"] = relationship(back_populates="alerts")
    acknowledger: Mapped["User | None"] = relationship(back_populates="alerts", foreign_keys=[acknowledged_by])
