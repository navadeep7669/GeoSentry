from __future__ import annotations
from datetime import datetime
from typing import Any
from sqlalchemy import String, DateTime, Float, JSON, Text, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry
from app.database import Base
from app.models.report import RiskLevel


class RiskZone(Base):
    __tablename__ = "risk_zones"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Zone boundary as PostGIS MULTIPOLYGON (SRID 4326)
    boundary: Mapped[Any] = mapped_column(
        Geometry("MULTIPOLYGON", srid=4326), nullable=False
    )

    # Centroid for quick distance queries
    centroid: Mapped[Any] = mapped_column(
        Geometry("POINT", srid=4326), nullable=True
    )

    # ── Base risk fields (Hackbros) ───────────────────────────────────────────
    risk_level: Mapped[RiskLevel] = mapped_column(
        String(20), nullable=False, default=RiskLevel.unknown
    )
    risk_score_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_score_max: Mapped[float | None] = mapped_column(Float, nullable=True)

    # IDs of reports that contributed to this zone
    report_ids: Mapped[list[int]] = mapped_column(JSON, default=list)

    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    # ── Dynamic Risk Engine fields (extended) ─────────────────────────────────
    # Optional external ID for linking to external data sources / zones.
    external_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )

    # Three-layer scoring: environment → exposure → priority
    environmental_risk: Mapped[float | None] = mapped_column(Float, nullable=True)
    exposure_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, index=True
    )

    # Human-readable explanation of the current risk level
    reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Latest hazard signal from the LHASA-style adapter
    last_hazard_probability: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Number of verified field reports associated with this zone
    field_report_count: Mapped[int] = mapped_column(Integer, default=0)

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<RiskZone id={self.id} risk={self.risk_level} priority={self.priority_score}>"