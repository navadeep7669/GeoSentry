from __future__ import annotations
import logging
from typing import Sequence
import firebase_admin
from firebase_admin import credentials, messaging

from app.config import settings

logger = logging.getLogger(__name__)

_initialized = False


def _init_firebase() -> bool:
    global _initialized
    if _initialized:
        return True
    try:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        _initialized = True
        return True
    except Exception as exc:
        logger.warning("Firebase init failed: %s — push notifications disabled", exc)
        return False


def send_push(fcm_tokens: Sequence[str], title: str, body: str, data: dict | None = None) -> tuple[int, list[str]]:
    """
    Send FCM multicast push notification.
    Returns (success_count, error_messages).
    """
    if not fcm_tokens:
        return 0, []

    if not _init_firebase():
        return 0, ["Firebase not configured"]

    token_list = [t for t in fcm_tokens if t]
    if not token_list:
        return 0, []

    try:
        message = messaging.MulticastMessage(
            tokens=list(token_list),
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            android=messaging.AndroidConfig(priority="high"),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(sound="default")
                )
            ),
        )
        response: messaging.BatchResponse = messaging.send_each_for_multicast(message)
        errors = [
            f"Token[{i}]: {r.exception}"
            for i, r in enumerate(response.responses)
            if not r.success
        ]
        logger.info("Push sent: %d/%d", response.success_count, len(token_list))
        return response.success_count, errors
    except Exception as exc:
        logger.error("Firebase send error: %s", exc)
        return 0, [str(exc)]
