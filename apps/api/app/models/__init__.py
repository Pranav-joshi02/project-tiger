"""SQLAlchemy model registry — import all models so Alembic can discover them."""
from app.db.session import Base

from app.models.user import User, UserRole
from app.models.reserve import Reserve
from app.models.station import Station, StationZone, StationStatus
from app.models.run import Run, RunStatus
from app.models.image import Image, ImageState
from app.models.detection import Detection, DetectionCategory
from app.models.flank import Flank, FlankSide
from app.models.embedding import Embedding
from app.models.tiger import Tiger, TigerStatus, TigerSex
from app.models.observation import Observation
from app.models.encounter import Encounter
from app.models.tiger_range import TigerRange, RangeMethod
from app.models.alert import Alert, AlertType, AlertSeverity, AlertStatus
from app.models.review import Review, ReviewState, ReviewDecisionType
from app.models.safari import (
    SafariRoute,
    SafariWaypoint,
    SightseeingZone,
    SafariSighting,
    SafariZone,
    WaypointType,
    ObserverType,
)

from app.models.camera_event import CameraEvent
from app.models.fingerprint import TigerFingerprintModel
from app.models.behavior_log import BehaviorLog
from app.models.audit_block import AuditBlock
from app.models.conflict_zone import ConflictRiskZone
from app.models.negative_constraint import NegativeConstraint

__all__ = [
    "Base",
    "User", "UserRole",
    "Reserve",
    "Station", "StationZone", "StationStatus",
    "Run", "RunStatus",
    "Image", "ImageState",
    "Detection", "DetectionCategory",
    "Flank", "FlankSide",
    "Embedding",
    "Tiger", "TigerStatus", "TigerSex",
    "Observation",
    "Encounter",
    "CameraEvent",
    "TigerFingerprintModel",
    "BehaviorLog",
    "AuditBlock",
    "ConflictRiskZone",
    "NegativeConstraint",
    "TigerRange", "RangeMethod",
    "Alert", "AlertType", "AlertSeverity", "AlertStatus",
    "Review", "ReviewState", "ReviewDecisionType",
    "SafariRoute", "SafariWaypoint", "SightseeingZone", "SafariSighting",
    "SafariZone", "WaypointType", "ObserverType",
]

