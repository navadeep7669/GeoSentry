from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, field_validator
from app.models.report import ReportStatus, RiskLevel


class ReportCreate(BaseModel):
    latitude: float
    longitude: float
    elevation_m: float | None = None
    description: str | None = None

    @field_validator("latitude")
    @classmethod
    def validate_lat(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_lon(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v


class ReportUpdate(BaseModel):
    """Validator PATCH payload."""
    status: ReportStatus | None = None
    validator_notes: str | None = None
    description: str | None = None


class ReporterMini(BaseModel):
    id: int
    email: str
    full_name: str | None

    model_config = {"from_attributes": True}


class ReportResponse(BaseModel):
    id: int
    user_id: int
    validated_by_id: int | None
    latitude: float
    longitude: float
    elevation_m: float | None
    description: str | None
    media_urls: list[str]
    status: ReportStatus
    validator_notes: str | None
    risk_score: float | None
    risk_level: RiskLevel
    rainfall_mm: float | None
    humidity_pct: float | None
    created_at: datetime
    updated_at: datetime
    risk_computed_at: datetime | None

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ReportResponse]
