from __future__ import annotations

from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RiskObservation(Base):
    """Immutable time-series snapshot for every monitoring pass.

    Each row represents the full state of a risk zone at a point in time.
    This allows trend analysis, escalation detection, and rate-of-change
    calculations without mutating the live risk_zones row.
    """

    __tablename__ = "risk_observations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    zone_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    location: Mapped[Any] = mapped_column(
        Geometry("POINT", srid=4326), nullable=False
    )

    # ── Environmental inputs ──────────────────────────────────────────────────
    rainfall_24h_mm: Mapped[float | None] = mapped_column(Float)
    rainfall_7d_mm: Mapped[float | None] = mapped_column(Float)
    soil_saturation: Mapped[float | None] = mapped_column(Float)
    slope_deg: Mapped[float | None] = mapped_column(Float)
    satellite_change: Mapped[float | None] = mapped_column(Float)
    historical_susceptibility: Mapped[float | None] = mapped_column(Float)

    # ── Exposure inputs ───────────────────────────────────────────────────────
    population_exposure: Mapped[float | None] = mapped_column(Float)
    road_importance: Mapped[float | None] = mapped_column(Float)
    critical_infrastructure: Mapped[float | None] = mapped_column(Float)
    rate_of_change: Mapped[float | None] = mapped_column(Float)

    # ── Computed scores ───────────────────────────────────────────────────────
    model_probability: Mapped[float | None] = mapped_column(Float)
    hazard_probability: Mapped[float | None] = mapped_column(Float)
    environmental_risk: Mapped[float | None] = mapped_column(Float)
    exposure_score: Mapped[float | None] = mapped_column(Float)
    priority_score: Mapped[float | None] = mapped_column(Float)
    risk_level: Mapped[str | None] = mapped_column(String(20))

    # ── Explainability ────────────────────────────────────────────────────────
    reasons: Mapped[str | None] = mapped_column(Text)          # semicolon-separated
    recommended_action: Mapped[str | None] = mapped_column(Text)