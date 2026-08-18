"""FastAPI application entrypoint for Pench Tiger Intelligence."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlalchemy as sa

from app.api import (
    alerts,
    auth,
    dashboard,
    health,
    images,
    live,
    maps,
    observations,
    reports,
    reviews,
    runs,
    safari,
    stations,
    tigers,
)
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine, Base, SessionLocal
from app.db.init_db import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    setup_logging()
    logger.info("Starting Pench Tiger Intelligence API")
    logger.info(f"Environment: {settings.app_env}")
    # Verify database connection, create extensions, create tables and auto-seed if needed
    try:
        with engine.connect() as conn:
            for ext in ["uuid-ossp", "postgis", "vector"]:
                try:
                    conn.execute(sa.text(f'CREATE EXTENSION IF NOT EXISTS "{ext}";'))
                    conn.commit()
                except Exception as ex:
                    logger.info(f"Extension '{ext}' not loaded (optional/pre-installed): {ex}")

        Base.metadata.create_all(bind=engine)
        logger.info("Database connection verified and tables synchronized")

        with SessionLocal() as db:
            init_db(db)
        logger.info("Database initialization and auto-seed verified")
    except Exception as e:
        logger.error(f"Database connection or initialization failed: {e}")
    yield
    logger.info("Shutting down API")


app = FastAPI(
    title="Pench Tiger Intelligence API",
    version="0.2.0",
    description="Camera-trap triage, tiger Re-ID, spatial intelligence, and conservation alerts.",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(runs.router)
app.include_router(images.router)
app.include_router(tigers.router)
app.include_router(observations.router)
app.include_router(stations.router)
app.include_router(reviews.router)
app.include_router(alerts.router)
app.include_router(maps.router)
app.include_router(reports.router)
app.include_router(live.router)
app.include_router(safari.router)
