"""Application configuration loaded from environment variables."""
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Application
    app_env: str = "development"
    secret_key: str = "change-me-before-deployment"

    # Database
    database_url: str = "postgresql+psycopg://pench:pench@localhost:5432/pench"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Storage
    storage_root: Path = Field(default=Path("storage"))

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minio"
    minio_secret_key: str = "miniosecret"
    minio_secure: bool = False
    minio_bucket_raw: str = "pench-raw"
    minio_bucket_quarantine: str = "pench-quarantine"
    minio_bucket_processed: str = "pench-processed"

    # Authentication
    jwt_secret: str = "dev-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # ML Models
    megadetector_version: str = "MDV6-mit-yolov9-c"
    triage_subject_threshold: float = 0.80
    triage_blank_threshold: float = 0.30

    # Re-ID
    reid_auto_threshold: float = 0.90
    reid_margin_threshold: float = 0.08
    reid_embedding_dim: int = 512

    # Spatial
    core_range_shift_threshold_km2: float = 15.0
    buffer_movement_threshold_km: float = 5.0

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


settings = Settings()
