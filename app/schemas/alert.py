from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.alert import AlertChannel, AlertStatus, AlertSeverity
from app.models.user import UserRole


class AlertCreate(BaseModel):
    zone_id: int | None = None
    title: str = "Urgent Landslide Advisory"
    severity: AlertSeverity = AlertSeverity.high
    location_name: str = "Monitored Landslide Corridor"
    latitude: float | None = None
    longitude: float | None = None
    probability_pct: float | None = None
    environmental_hazard: float | None = None
    priority_score: float | None = None
    impact_summary: str | None = None
    reasons: list[str] = Field(default_factory=list)
    recommended_action: str | None = None
    message: str
    channel: AlertChannel = AlertChannel.both
    geofence_wkt: str | None = None
    target_roles: list[UserRole] = [UserRole.citizen]
    recipient_groups: list[str] = Field(default_factory=lambda: ["authorities", "citizens"])


class AlertAcknowledgeRequest(BaseModel):
    acknowledged_by: str = "District Emergency Officer"
    notes: str | None = "Acknowledged by district disaster cell."


class AlertResponseActionRequest(BaseModel):
    status: AlertStatus = AlertStatus.in_progress
    response_action: str = "Disaster response unit deployed to sector."
    actor: str = "Emergency Operations Command"


class AlertEscalateRequest(BaseModel):
    escalated_to: str = "State Disaster Management Authority (SDMA)"
    escalation_reason: str = "Uncontained slope failure / persistent rainfall surge."


class AlertResponse(BaseModel):
    id: int
    authority_id: int
    zone_id: int | None = None
    title: str = "Landslide Risk Alert"
    severity: AlertSeverity = AlertSeverity.high
    location_name: str = "Monitored Landslide Corridor"
    latitude: float | None = None
    longitude: float | None = None
    probability_pct: float | None = None
    environmental_hazard: float | None = None
    priority_score: float | None = None
    impact_summary: str | None = None
    reasons: list[str] = Field(default_factory=list)
    recommended_action: str | None = None
    message: str
    channel: AlertChannel = AlertChannel.both
    status: AlertStatus = AlertStatus.new
    geofence_wkt: str | None = None
    target_roles: list[str] = Field(default_factory=list)
    recipient_groups: list[str] = Field(default_factory=list)
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None
    response_action: str | None = None
    escalated: bool = False
    escalated_at: datetime | None = None
    timeline: list[dict] = Field(default_factory=list)
    recipient_count: int = 0
    sms_sent: int = 0
    push_sent: int = 0
    errors: list[str] = Field(default_factory=list)
    dispatched_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
