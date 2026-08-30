from __future__ import annotations
import logging
from datetime import datetime, timezone

from sqlalchemy import select, text, create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.tasks.celery_app import celery_app
from app.models.alert import Alert, AlertStatus
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

_sync_engine = None


def _get_engine():
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(settings.SYNC_DATABASE_URL, pool_pre_ping=True)
    return _sync_engine


@celery_app.task(name="alert_tasks.dispatch_alert", bind=True, max_retries=2, default_retry_delay=30)
def dispatch_alert(self, alert_id: int) -> dict:
    """
    1. Load Alert record
    2. Find target users (by geofence + role)
    3. Batch send SMS (Twilio) + push (Firebase)
    4. Update Alert record with counts and status
    """
    from app.services.sms_service import send_sms
    from app.services.push_service import send_push

    engine = _get_engine()
    with Session(engine) as session:
        alert = session.get(Alert, alert_id)
        if alert is None:
            logger.error("Alert %d not found", alert_id)
            return {"error": f"Alert {alert_id} not found"}

        alert.status = AlertStatus.dispatching
        session.commit()

        # Build user query with optional geofence + role filters
        stmt = select(User).where(User.is_active == True)

        target_roles = alert.target_roles or []
        if target_roles:
            stmt = stmt.where(User.role.in_(target_roles))

        geofence_wkt = alert.geofence_wkt
        if geofence_wkt:
            # Filter users whose last location is in the geofence
            # Using parameter binding to prevent SQL injection
            stmt = stmt.join(
                User.reports
            ).where(
                text(
                    "ST_Within(reports.location, ST_GeomFromText(:wkt, 4326))"
                )
            ).params(wkt=geofence_wkt).distinct()

        users = session.execute(stmt).scalars().all()

        phones = [u.phone for u in users if u.phone]
        fcm_tokens = [u.fcm_token for u in users if u.fcm_token]

        total = len(users)
        all_errors: list[str] = []
        sms_sent = 0
        push_sent = 0

        if alert.channel.value in ("sms", "both") and phones:
            sms_sent, sms_errors = send_sms(phones, alert.message)
            all_errors.extend(sms_errors)

        if alert.channel.value in ("push", "both") and fcm_tokens:
            push_sent, push_errors = send_push(
                fcm_tokens,
                title="🚨 Landslide Alert",
                body=alert.message,
                data={"alert_id": str(alert_id)},
            )
            all_errors.extend(push_errors)

        alert.status = AlertStatus.completed
        alert.recipient_count = total
        alert.sms_sent = sms_sent
        alert.push_sent = push_sent
        alert.errors = all_errors
        alert.dispatched_at = datetime.now(tz=timezone.utc)
        session.commit()

        logger.info(
            "Alert %d dispatched: %d recipients, %d SMS, %d push, %d errors",
            alert_id, total, sms_sent, push_sent, len(all_errors),
        )

    return {
        "alert_id": alert_id,
        "recipients": total,
        "sms_sent": sms_sent,
        "push_sent": push_sent,
        "errors": len(all_errors),
    }
