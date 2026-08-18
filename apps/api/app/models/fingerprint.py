import uuid
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import Column, String, Float, ForeignKey, DateTime, JSON
from app.db.session import Base
from sqlalchemy.sql import func


class TigerFingerprintModel(Base):
    __tablename__ = "tiger_fingerprints"

    id = Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    tiger_id = Column(sa.Uuid, ForeignKey("tigers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Biometric features
    stripe_pattern_encoding = Column(JSON, nullable=True, comment="Encoded stripe pattern features")
    facial_features_encoding = Column(JSON, nullable=True, comment="Encoded facial features")
    flank_features_encoding = Column(JSON, nullable=True, comment="Encoded flank features")
    
    # Metadata
    feature_dim = Column(sa.Integer, nullable=False, default=512)
    model_version = Column(String(50), nullable=False)
    extraction_date = Column(DateTime(timezone=True), server_default=func.now())
    quality_score = Column(Float, nullable=True, comment="0.0 to 1.0 confidence score of extraction")
