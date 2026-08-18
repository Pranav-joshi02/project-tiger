"""Tiger individual identity model."""
import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class TigerStatus(str, enum.Enum):
    PROVISIONAL = "PROVISIONAL"
    CONFIRMED = "CONFIRMED"
    MERGED = "MERGED"
    ARCHIVED = "ARCHIVED"


class TigerSex(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    UNKNOWN = "UNKNOWN"


class Tiger(Base):
    __tablename__ = "tigers"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    reserve_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("reserves.id"), nullable=True)
    name: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    code: Mapped[str] = mapped_column(sa.String(50), nullable=False, unique=True, index=True)
    sex: Mapped[TigerSex] = mapped_column(sa.Enum(TigerSex, native_enum=False), default=TigerSex.UNKNOWN)
    status: Mapped[TigerStatus] = mapped_column(sa.Enum(TigerStatus, native_enum=False), default=TigerStatus.PROVISIONAL)
    merged_into_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("tigers.id"), nullable=True)
    first_seen: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    total_observations: Mapped[int] = mapped_column(sa.Integer, default=0)
    confirmed_observations: Mapped[int] = mapped_column(sa.Integer, default=0)
    left_prototype_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("embeddings.id"), nullable=True)
    right_prototype_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("embeddings.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())

    # Relationships
    reserve: Mapped["Reserve | None"] = relationship(back_populates="tigers")
    observations: Mapped[list["Observation"]] = relationship(back_populates="tiger")
    embeddings: Mapped[list["Embedding"]] = relationship(back_populates="tiger", foreign_keys="Embedding.tiger_id")
    ranges: Mapped[list["TigerRange"]] = relationship(back_populates="tiger")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="tiger")
    left_prototype: Mapped["Embedding | None"] = relationship(foreign_keys=[left_prototype_id])
    right_prototype: Mapped["Embedding | None"] = relationship(foreign_keys=[right_prototype_id])
