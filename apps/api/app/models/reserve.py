"""Wildlife reserve model with boundary geometry."""
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Reserve(Base):
    __tablename__ = "reserves"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(sa.String(50), nullable=False, unique=True)
    boundary = mapped_column(sa.JSON, nullable=True)
    core_boundary = mapped_column(sa.JSON, nullable=True)
    buffer_boundary = mapped_column(sa.JSON, nullable=True)
    area_km2: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationships
    stations: Mapped[list["Station"]] = relationship(back_populates="reserve")
    tigers: Mapped[list["Tiger"]] = relationship(back_populates="reserve")
