from __future__ import annotations
import enum
from datetime import datetime
from sqlalchemy import String, Enum, DateTime, Integer, Float, ForeignKey, Text, JSON, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AlertChannel(str, enum.Enum):
    sms = "sms"
    push = "push"
    both = "both"


class AlertSeverity(str, enum.Enum):
    low = "low"
    moderate = "moderate"
    high = "high"
    critical = "critical"


class AlertStatus(str, enum.Enum):
    new = "new"
    acknowledged = "acknowledged"
    in_progress = "in_progress"
    resolved = "resolved"
    cancelled = "cancelled"
    pending = "pending"
    dispatching = "dispatching"
    completed = "completed"
    failed = "failed"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    authority_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    zone_id: Mapped[int | None] = mapped_column(ForeignKey("risk_zones.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(255), default="Landslide Risk Alert")
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, name="alertseverity"),
        nullable=False,
        default=AlertSeverity.high,
    )
    location_name: Mapped[str] = mapped_column(String(255), default="Monitored Landslide Sector")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Scientific Risk Metrics
    probability_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    environmental_hazard: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    impact_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)

    message: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[AlertChannel] = mapped_column(
        Enum(AlertChannel, name="alertchannel"),
        nullable=False,
        default=AlertChannel.both,
    )
    status: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus, name="alertstatus"),
        nullable=False,
        default=AlertStatus.new,
    )

    # Targeting & Recipient Groups
    geofence_wkt: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    recipient_groups: Mapped[list[str]] = mapped_column(JSON, default=lambda: ["authorities", "citizens"])

    # Acknowledgement & Escalation Tracking
    acknowledged_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    response_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timeline: Mapped[list[dict]] = mapped_column(JSON, default=list)

    # Delivery Metrics
    recipient_count: Mapped[int] = mapped_column(Integer, default=0)
    sms_sent: Mapped[int] = mapped_column(Integer, default=0)
    push_sent: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[list[str]] = mapped_column(JSON, default=list)

    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    authority: Mapped["User"] = relationship(back_populates="alerts_sent")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Alert id={self.id} severity={self.severity} status={self.status} location={self.location_name}>"
