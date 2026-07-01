"""Tests for the health and readiness endpoints."""

from __future__ import annotations

from httpx import AsyncClient

from app.core.config import settings

PREFIX = settings.API_V1_PREFIX


async def test_health_ok(client: AsyncClient) -> None:
    response = await client.get(f"{PREFIX}/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["environment"] == "development"


async def test_ready_checks_database(client: AsyncClient) -> None:
    response = await client.get(f"{PREFIX}/ready")
    assert response.status_code == 200
    assert response.json()["database"] == "connected"


async def test_root_returns_metadata(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == settings.PROJECT_NAME
