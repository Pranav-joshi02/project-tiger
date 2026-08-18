"""Safari routes, waypoints, sightseeing zones, and field sightings models."""
import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class SafariZone(str, enum.Enum):
    TOURIA = "TOURIA"
    KARMAJHIRI = "KARMAJHIRI"
    GUMTARA = "GUMTARA"
    KHURSAPAR = "KHURSAPAR"
    RUKHAD = "RUKHAD"
    JAMTARA = "JAMTARA"


class WaypointType(str, enum.Enum):
    GATE = "GATE"
    WATERHOLE = "WATERHOLE"
    MEADOW = "MEADOW"
    RIDGE = "RIDGE"
    RIVERBED = "RIVERBED"
    CHECKPOST = "CHECKPOST"


class ObserverType(str, enum.Enum):
    GYPSY_NATURALIST = "GYPSY_NATURALIST"
    FOREST_GUARD = "FOREST_GUARD"
    CAMERA_TRAP = "CAMERA_TRAP"
    TOURIST_GROUP = "TOURIST_GROUP"


class SafariRoute(Base):
    __tablename__ = "safari_routes"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(sa.String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    zone: Mapped[SafariZone] = mapped_column(sa.Enum(SafariZone, native_enum=False), nullable=False)
    gate_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    visibility_rating: Mapped[int] = mapped_column(sa.Integer, default=85)
    distance_km: Mapped[float] = mapped_column(sa.Float, default=25.0)
    duration_hours: Mapped[float] = mapped_column(sa.Float, default=3.5)
    terrain_difficulty: Mapped[str] = mapped_column(sa.String(50), default="MODERATE")
    slot_recommendation: Mapped[str] = mapped_column(sa.String(50), default="BOTH")
    max_vehicles: Mapped[int] = mapped_column(sa.Integer, default=25)
    current_vehicles_booked: Mapped[int] = mapped_column(sa.Integer, default=15)
    summary: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    highlights: Mapped[dict | list | None] = mapped_column(sa.JSON, nullable=True)
    resident_tigers: Mapped[dict | list | None] = mapped_column(sa.JSON, nullable=True)
    naturalist_tips: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    suggested_lens: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationships
    waypoints: Mapped[list["SafariWaypoint"]] = relationship(
        back_populates="route", cascade="all, delete-orphan", order_by="SafariWaypoint.order"
    )
    sightings: Mapped[list["SafariSighting"]] = relationship(
        back_populates="route", cascade="all, delete-orphan"
    )


class SafariWaypoint(Base):
    __tablename__ = "safari_waypoints"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    route_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("safari_routes.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(sa.Float, nullable=False)
    longitude: Mapped[float] = mapped_column(sa.Float, nullable=False)
    order: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)
    type: Mapped[WaypointType] = mapped_column(sa.Enum(WaypointType, native_enum=False), default=WaypointType.MEADOW)
    tiger_sighting_chance: Mapped[int] = mapped_column(sa.Integer, default=70)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationships
    route: Mapped["SafariRoute"] = relationship(back_populates="waypoints")


class SightseeingZone(Base):
    __tablename__ = "sightseeing_zones"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(sa.String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    zone_type: Mapped[str] = mapped_column(sa.String(50), default="CORE")
    latitude: Mapped[float] = mapped_column(sa.Float, nullable=False)
    longitude: Mapped[float] = mapped_column(sa.Float, nullable=False)
    radius_meters: Mapped[int] = mapped_column(sa.Integer, default=1000)
    visibility_score_morning: Mapped[int] = mapped_column(sa.Integer, default=90)
    visibility_score_afternoon: Mapped[int] = mapped_column(sa.Integer, default=85)
    visibility_score_night: Mapped[int] = mapped_column(sa.Integer, default=50)
    primary_habitat: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    resident_tigers: Mapped[dict | list | None] = mapped_column(sa.JSON, nullable=True)
    key_landmarks: Mapped[dict | list | None] = mapped_column(sa.JSON, nullable=True)
    recommended_gate: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    best_safari_timing: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())


class SafariSighting(Base):
    __tablename__ = "safari_sightings"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    route_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("safari_routes.id"), nullable=True)
    tiger_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("tigers.id"), nullable=True, index=True)
    tiger_code: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    tiger_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    location_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(sa.Float, nullable=False)
    longitude: Mapped[float] = mapped_column(sa.Float, nullable=False)
    observed_by: Mapped[ObserverType] = mapped_column(sa.Enum(ObserverType, native_enum=False), default=ObserverType.GYPSY_NATURALIST)
    behavior: Mapped[str] = mapped_column(sa.Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(sa.Float, default=0.95)
    photo_url: Mapped[str | None] = mapped_column(sa.String(1024), nullable=True)
    captured_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationships
    route: Mapped["SafariRoute | None"] = relationship(back_populates="sightings")
    tiger: Mapped["Tiger | None"] = relationship()
