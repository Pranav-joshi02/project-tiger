"""Health check endpoint."""
from fastapi import APIRouter
import sqlalchemy as sa

from app.db.session import engine

router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    """Application health check."""
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(sa.text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if db_ok else "degraded",
        "service": "pench-tiger-intelligence-api",
        "database": "connected" if db_ok else "unavailable",
        "data_notice": "synthetic demonstration data",
    }
