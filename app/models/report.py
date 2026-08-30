from __future__ import annotations
import enum
from datetime import datetime
from typing import Any
from sqlalchemy import String, Enum, DateTime, Float, ForeignKey, JSON, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from app.database import Base


class ReportStatus(str, enum.Enum):
    pending = "pending"
    validated = "validated"
    rejected = "rejected"


class RiskLevel(str, enum.Enum):
    low = "Low"
    moderate = "Moderate"
    high = "High"
    critical = "Critical"
    unknown = "Unknown"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    validated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Location stored as PostGIS POINT (lon, lat, SRID 4326)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    elevation_m: Mapped[float | None] = mapped_column(Float, nullable=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_urls: Mapped[list[str]] = mapped_column(JSON, default=list)

    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, name="reportstatus"),
        default=ReportStatus.pending,
        nullable=False,
    )
    validator_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Risk computed by Celery after validation
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, name="risklevel"),
        default=RiskLevel.unknown,
        nullable=False,
    )

    # Weather snapshot at time of risk computation
    rainfall_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    risk_computed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    reporter: Mapped["User"] = relationship(  # noqa: F821
        back_populates="reports", foreign_keys=[user_id]
    )
    validator: Mapped["User | None"] = relationship(  # noqa: F821
        back_populates="validated_reports", foreign_keys=[validated_by_id]
    )

    def __repr__(self) -> str:
        return f"<Report id={self.id} status={self.status} risk={self.risk_level}>"
