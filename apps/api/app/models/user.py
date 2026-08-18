"""User model with role-based access control."""
import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    FOREST_OFFICER = "FOREST_OFFICER"
    RESEARCHER = "RESEARCHER"
    REVIEWER = "REVIEWER"
    VIEWER = "VIEWER"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(sa.String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(sa.Enum(UserRole, native_enum=False), nullable=False, default=UserRole.VIEWER)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())

    # Relationships
    reviews: Mapped[list["Review"]] = relationship(back_populates="reviewer")
    runs: Mapped[list["Run"]] = relationship(back_populates="creator")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="acknowledger")
