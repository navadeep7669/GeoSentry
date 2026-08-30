from __future__ import annotations
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Query, Depends

logger = logging.getLogger(__name__)

from app.models.alert import Alert, AlertStatus, AlertSeverity
from app.models.risk_zone import RiskZone
from app.schemas.alert import (
    AlertCreate,
    AlertResponse,
    AlertAcknowledgeRequest,
    AlertResponseActionRequest,
    AlertEscalateRequest,
)
from app.dependencies import DB, OptionalUser, AuthorityOnly
from app.models.user import User
from app.services.alert_service import alert_service

router = APIRouter()


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    payload: AlertCreate,
    current_user: OptionalUser = None,
):
    """
    Dispatch or generate a role-based emergency landslide alert.
    - Automated deduplication within cooldown window
    - Recipient routing across citizens, authorities, medical, validators, and higher officials
    - Fires background Celery task for Twilio SMS + Firebase push
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to dispatch emergency broadcasts.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = current_user.id

    alert_dict = alert_service.create_alert(payload.model_dump(), authority_id=user_id)

    # Trigger Celery async task non-blockingly
    try:
        from app.tasks.alert_tasks import dispatch_alert
        dispatch_alert.apply_async(args=[alert_dict["id"]], queue="alerts", retry=False)
    except Exception as exc:
        logger.debug("Celery broker offline or not responding: %s", exc)

    return AlertResponse(**alert_dict)


@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    role: Optional[str] = Query(None, description="Filter by recipient role: citizen, authority, medical, higher_official, all"),
    severity: Optional[str] = Query(None, description="Filter by severity: critical, high, moderate, low, all"),
    current_user: OptionalUser = None,
):
    """
    List active emergency alerts with role-based visibility filtering.
    """
    user_role = role or (current_user.role.value if current_user else "all")
    alerts = alert_service.get_all_alerts(role=user_role, severity=severity)
    return [AlertResponse(**a) for a in alerts]


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: int):
    """
    Get full details, environmental context, recipient groups, and audit timeline for an alert.
    """
    alert = alert_service.get_alert_by_id(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResponse(**alert)


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    payload: AlertAcknowledgeRequest,
    current_user: OptionalUser = None,
):
    """
    Acknowledge an emergency alert to create accountability and update audit trail.
    """
    user_name = current_user.full_name or current_user.email if current_user else payload.acknowledged_by
    alert = alert_service.acknowledge_alert(alert_id, user_name=user_name, notes=payload.notes)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResponse(**alert)


@router.post("/{alert_id}/response", response_model=AlertResponse)
async def update_response_status(
    alert_id: int,
    payload: AlertResponseActionRequest,
    current_user: OptionalUser = None,
):
    """
    Update response state: IN_PROGRESS, RESOLVED, or CANCELLED with operational notes.
    """
    actor = current_user.full_name or current_user.email if current_user else payload.actor
    alert = alert_service.update_response_status(alert_id, status=payload.status.value, action=payload.response_action, actor=actor)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResponse(**alert)


@router.post("/{alert_id}/escalate", response_model=AlertResponse)
async def escalate_alert(
    alert_id: int,
    payload: AlertEscalateRequest,
    current_user: OptionalUser = None,
):
    """
    Escalate a critical or unacknowledged emergency alert to State/NDMA Higher Officials.
    """
    alert = alert_service.escalate_alert(alert_id, escalated_to=payload.escalated_to, reason=payload.escalation_reason)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResponse(**alert)
