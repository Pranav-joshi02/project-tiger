import uuid
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import Column, String, DateTime
from app.db.session import Base
from sqlalchemy.sql import func


class AuditBlock(Base):
    __tablename__ = "merkle_audit_blocks"

    id = Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    block_index = Column(sa.Integer, nullable=False, unique=True, index=True)
    timestamp = Column(String, nullable=False)
    previous_hash = Column(String(64), nullable=False)
    merkle_root = Column(String(64), nullable=False)
    records_hash = Column(String(64), nullable=False)
    signature = Column(String, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
