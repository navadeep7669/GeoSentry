from __future__ import annotations
import logging
from typing import Sequence
from twilio.rest import Client
from app.config import settings

logger = logging.getLogger(__name__)

_twilio_client: Client | None = None


def _get_client() -> Client | None:
    global _twilio_client
    if _twilio_client is None and settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
        _twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    return _twilio_client


def send_sms(to_numbers: Sequence[str], body: str) -> tuple[int, list[str]]:
    """
    Send SMS to a list of phone numbers.
    Returns (success_count, error_messages).
    """
    client = _get_client()
    if client is None:
        logger.warning("Twilio not configured — SMS skipped for %d recipients", len(to_numbers))
        return 0, ["Twilio credentials not configured"]

    sent = 0
    errors: list[str] = []
    for number in to_numbers:
        if not number:
            continue
        try:
            client.messages.create(
                body=body,
                from_=settings.TWILIO_FROM_NUMBER,
                to=number,
            )
            sent += 1
        except Exception as exc:
            logger.error("SMS to %s failed: %s", number, exc)
            errors.append(f"SMS to {number}: {exc}")

    logger.info("SMS sent: %d/%d", sent, len(to_numbers))
    return sent, errors
