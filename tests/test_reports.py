from __future__ import annotations
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_create_report_requires_auth():
    """POST /reports without token -> 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/reports", data={"latitude": "18.5", "longitude": "73.8"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_list_reports_requires_auth():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/reports")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_risk_zones_requires_auth():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/risk-zones")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_alerts_requires_authority():
    """POST /alerts without auth -> 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/alerts", json={"message": "test"})
    assert r.status_code == 401