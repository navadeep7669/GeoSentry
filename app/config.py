from __future__ import annotations
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "GeoSentry"
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = (
        "postgresql+asyncpg://landslide:landslide@localhost:5432/landslide_db"
    )
    SYNC_DATABASE_URL: str = (
        "postgresql+psycopg2://landslide:landslide@localhost:5432/landslide_db"
    )

    # ── Redis / Celery ────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # ── Storage (S3 / MinIO) ──────────────────────────────────────────────────
    STORAGE_ENDPOINT_URL: Optional[str] = "http://localhost:9000"
    STORAGE_ACCESS_KEY: str = "minioadmin"
    STORAGE_SECRET_KEY: str = "minioadmin"
    STORAGE_BUCKET_NAME: str = "landslide-media"
    STORAGE_REGION: str = "us-east-1"

    # ── AI / LLM (OpenRouter / Gemini) ──────────────────────────────────────────
    OPENROUTER_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # ── Weather ───────────────────────────────────────────────────────────────
    OPENWEATHER_API_KEY: str = ""

    # ── Twilio ────────────────────────────────────────────────────────────────
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    # ── Firebase ──────────────────────────────────────────────────────────────
    FIREBASE_CREDENTIALS_PATH: str = "firebase_credentials.json"

    # ── ML ────────────────────────────────────────────────────────────────────
    MODEL_PATH: str = "app/ml/model.pkl"

    # ── Dynamic Risk Engine ──────────────────────────────────────────────────
    # Thresholds for classifying the composite priority score (0-100).
    # Kept separate from ML model parameters — these are operational decisions.
    RISK_HIGH_THRESHOLD: float = 51.0
    RISK_CRITICAL_THRESHOLD: float = 76.0

    # Each verified field report near a zone raises its risk by this many points
    # (capped at FIELD_REPORT_MAX_BOOST to prevent runaway scores).
    FIELD_REPORT_RISK_BOOST: float = 6.0
    FIELD_REPORT_MAX_BOOST: float = 18.0

    # ── Continuous Monitoring ────────────────────────────────────────────────
    # How often the monitoring Celery beat task runs (minutes).
    MONITORING_INTERVAL_MINUTES: int = 15

    # ── Satellite / Earth Observation (optional, future) ─────────────────────
    # Set GEE_PROJECT + GEE_SERVICE_ACCOUNT_JSON to enable Earth Engine ingestion.
    GEE_PROJECT: str = ""
    GEE_SERVICE_ACCOUNT_JSON: str = ""
    SATELLITE_PROVIDER: str = "external"  # "gee" | "sentinel" | "external"


settings = Settings()