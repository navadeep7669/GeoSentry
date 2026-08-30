from __future__ import annotations
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.database import get_db


# ── DB override ────────────────────────────────────────────────────────────────

def make_mock_db():
    """Async session mock — simulates no pre-existing user in DB."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    mock_session.flush = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    # refresh sets minimal attrs so UserResponse.model_validate succeeds
    async def fake_refresh(obj):
        obj.id = 1
        obj.email = getattr(obj, "email", "test@example.com")
        obj.full_name = getattr(obj, "full_name", None)
        obj.phone = getattr(obj, "phone", None)
        obj.role = getattr(obj, "role", "citizen")
        obj.is_active = True
        from datetime import datetime, timezone
        obj.created_at = datetime.now(tz=timezone.utc)

    mock_session.refresh = fake_refresh
    return mock_session


async def override_get_db():
    yield make_mock_db()


# ── Tests ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_success():
    """Register a new citizen — fully mocked DB, no Postgres needed."""
    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post("/auth/register", json={
                "email": "citizen@example.com",
                "password": "securepass123",
                "role": "citizen",
                "full_name": "Test Citizen",
            })
        assert r.status_code == 201
        data = r.json()
        assert "access_token" in data
        assert data["user"]["email"] == "citizen@example.com"
        assert data["user"]["role"] == "citizen"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_register_invalid_email():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "securepass123",
        })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_register_weak_password():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/auth/register", json={
            "email": "user@example.com",
            "password": "short",
        })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_login_missing_password_field():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/auth/login", json={"email": "x@y.com"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_login_wrong_credentials():
    """Login with wrong credentials against mocked DB → 401."""
    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post("/auth/login", json={
                "email": "nobody@example.com",
                "password": "wrongpassword",
            })
        assert r.status_code == 401
    finally:
        app.dependency_overrides.clear()