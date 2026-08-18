"""Celery application configuration."""
import os

from celery import Celery
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Celery app
celery_app = Celery("pench")
app = celery_app
celery = celery_app
celery_app.config_from_object({
    "broker_url": os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0")),
    "result_backend": os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "task_track_started": True,
    "task_routes": {
        "workers.tasks.ingestion.*": {"queue": "ingestion"},
        "workers.tasks.deduplication.*": {"queue": "ingestion"},
        "workers.tasks.triage.*": {"queue": "triage"},
        "workers.tasks.species_detection.*": {"queue": "detection"},
        "workers.tasks.tiger_detection.*": {"queue": "detection"},
        "workers.tasks.flank_extraction.*": {"queue": "detection"},
        "workers.tasks.encounter_grouping.*": {"queue": "detection"},
        "workers.tasks.embedding.*": {"queue": "reid"},
        "workers.tasks.reid.*": {"queue": "reid"},
        "workers.tasks.spatial.*": {"queue": "spatial"},
        "workers.tasks.alerts.*": {"queue": "alerts"},
        "workers.tasks.reports.*": {"queue": "reports"},
    },
    "include": [
        "workers.tasks.ingestion",
        "workers.tasks.deduplication",
        "workers.tasks.triage",
        "workers.tasks.species_detection",
        "workers.tasks.tiger_detection",
        "workers.tasks.flank_extraction",
        "workers.tasks.encounter_grouping",
        "workers.tasks.embedding",
        "workers.tasks.reid",
        "workers.tasks.spatial",
        "workers.tasks.alerts",
        "workers.tasks.reports",
    ],
})


# Database session factory for workers
_engine = None
_SessionFactory = None


def get_worker_db():
    """Get a database session for use in Celery tasks."""
    global _engine, _SessionFactory
    if _engine is None:
        db_url = os.getenv("DATABASE_URL", "postgresql+psycopg://pench:pench@localhost:5432/pench")
        _engine = create_engine(db_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
        
        @event.listens_for(_engine, "connect")
        def _register_pgvector(dbapi_conn, connection_record):
            try:
                from pgvector.psycopg import register_vector
                register_vector(dbapi_conn)
            except Exception:
                pass

        _SessionFactory = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _SessionFactory()
