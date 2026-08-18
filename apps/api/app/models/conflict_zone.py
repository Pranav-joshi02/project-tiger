import uuid
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import Column, String, Float, DateTime, JSON
from app.db.session import Base
from sqlalchemy.sql import func
try:
    from geoalchemy2 import Geometry
except ImportError:
    Geometry = None


class ConflictRiskZone(Base):
    __tablename__ = "conflict_risk_zones"

    id = Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    
    # Spatial data
    geom = Column(Geometry('POLYGON', srid=4326) if Geometry is not None else String, nullable=False, index=True)
    zone_name = Column(String(200), nullable=True)
    
    # Risk factors
    risk_level = Column(String(50), nullable=False, index=True, comment="LOW, MEDIUM, HIGH, CRITICAL")
    risk_score = Column(Float, nullable=False)
    
    # Model factors contributing to risk
    contributing_factors = Column(JSON, nullable=True)
    model_version = Column(String(50), nullable=False)
    
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True), nullable=True)
