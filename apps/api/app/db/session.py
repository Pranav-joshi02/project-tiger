"""Database session management.

Synchronous SQLAlchemy with psycopg driver for PostgreSQL.
PostGIS and pgvector extensions are assumed to be pre-configured.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


# Patch pgvector.vector.Vector._from_db to handle psycopg3 returning list/ndarray
try:
    import pgvector.vector
    _orig_from_db = pgvector.vector.Vector._from_db

    def _safe_from_db(cls, value):
        if value is None:
            return None
        if isinstance(value, list):
            return [float(x) for x in value]
        if hasattr(value, "tolist"):
            return [float(x) for x in value.tolist()]
        return _orig_from_db(value)

    pgvector.vector.Vector._from_db = classmethod(_safe_from_db)
except Exception:
    pass


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.is_development,
)


@event.listens_for(engine, "connect")
def _register_pgvector(dbapi_conn, connection_record):
    """Register pgvector type adapters for psycopg connections."""
    try:
        from pgvector.psycopg import register_vector
        register_vector(dbapi_conn)
    except Exception:
        pass  # non-fatal if extension not loaded yet

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
