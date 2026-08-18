import uuid
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import Column, String, Float, ForeignKey, DateTime, JSON
from app.db.session import Base
from sqlalchemy.sql import func


class BehaviorLog(Base):
    __tablename__ = "behavior_logs"

    id = Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    observation_id = Column(sa.Uuid, ForeignKey("observations.id", ondelete="CASCADE"), nullable=False, index=True)
    tiger_id = Column(sa.Uuid, ForeignKey("tigers.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Classification details
    behavior_class = Column(String(100), nullable=False, index=True, comment="e.g., resting, walking, hunting, mating")
    confidence_score = Column(Float, nullable=False)
    model_version = Column(String(50), nullable=False)
    
    # Context
    temporal_context = Column(JSON, nullable=True, comment="Sequence information if extracted from video")
    notes = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
