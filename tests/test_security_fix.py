from __future__ import annotations
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from app.main import app
from app.database import get_db
from app.models.user import UserRole
from datetime import datetime, timezone

def make_mock_db():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    mock_session.flush = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    async def fake_refresh(obj):
        obj.id = 1
        obj.email = getattr(obj, "email", "test@example.com")
        obj.full_name = getattr(obj, "full_name", None)
        obj.phone = getattr(obj, "phone", None)
        # We don't override the role here because we want to see what the router set
        obj.is_active = True
        obj.created_at = datetime.now(tz=timezone.utc)

    mock_session.refresh = fake_refresh
    return mock_session

async def override_get_db():
    yield make_mock_db()

@pytest.mark.asyncio
async def test_register_privilege_escalation_fix():
    """Verify that an attempt to register as authority results in citizen role."""
    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Even if the client sends "role": "authority"
            r = await client.post("/auth/register", json={
                "email": "attacker@example.com",
                "password": "securepass123",
                "role": "authority",
                "full_name": "Attacker",
            })
        assert r.status_code == 201
        data = r.json()
        # The returned role MUST be citizen
        assert data["user"]["role"] == "citizen"
    finally:
        app.dependency_overrides.clear()
