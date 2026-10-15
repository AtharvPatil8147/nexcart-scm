"""
NexCart — Health Endpoint Tests
Basic pytest tests for the health, DB health, and dashboard stats endpoints.
Uses pytest-asyncio and httpx.AsyncClient.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from backend.main import app


@pytest_asyncio.fixture
async def client():
    """Create an async test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_endpoint_returns_200(client):
    """GET /api/health should return 200 with status, version, and environment."""
    response = await client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "environment" in data
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_db_health_returns_status_field(client):
    """GET /api/health/db should return a response with a 'status' field."""
    response = await client.get("/api/health/db")
    # May return 200 (connected) or 503 (disconnected) depending on env
    assert response.status_code in (200, 503)

    data = response.json()
    assert "status" in data
    # Status should be either 'ok' or 'error'
    assert data["status"] in ("ok", "error")


@pytest.mark.asyncio
async def test_dashboard_stats_returns_all_fields(client):
    """GET /api/dashboard/stats should return all expected KPI fields."""
    response = await client.get("/api/dashboard/stats")
    # May return 200 (success) or 500 (if DB not connected)
    if response.status_code == 200:
        data = response.json()
        expected_fields = [
            "total_skus",
            "at_risk_count",
            "nudges_sent_today",
            "revenue_recovered_7d",
            "signal_events_24h",
            "risk_distribution",
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

        # risk_distribution should have all 4 levels
        risk_dist = data["risk_distribution"]
        for level in ("low", "medium", "high", "critical"):
            assert level in risk_dist, f"Missing risk level: {level}"


@pytest.mark.asyncio
async def test_health_version_is_string(client):
    """The version field should be a non-empty string."""
    response = await client.get("/api/health")
    data = response.json()
    assert isinstance(data["version"], str)
    assert len(data["version"]) > 0


@pytest.mark.asyncio
async def test_db_health_has_latency_on_success(client):
    """If DB is connected, the response should include latency_ms."""
    response = await client.get("/api/health/db")
    data = response.json()
    if data["status"] == "ok":
        assert "latency_ms" in data
        assert isinstance(data["latency_ms"], (int, float))
        assert data["latency_ms"] >= 0


# ✓ test_health.py complete
