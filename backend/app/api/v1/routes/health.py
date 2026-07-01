"""Health & readiness endpoints for load balancers and uptime checks."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app import __version__
from app.api.deps import SessionDep
from app.core.config import settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    environment: str
    version: str


class ReadinessResponse(BaseModel):
    status: str
    database: str


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health() -> HealthResponse:
    """Cheap liveness check — the process is up and serving requests."""
    return HealthResponse(
        status="ok",
        environment=settings.ENVIRONMENT.value,
        version=__version__,
    )


@router.get("/ready", response_model=ReadinessResponse, summary="Readiness probe")
async def ready(session: SessionDep) -> ReadinessResponse:
    """Readiness check — verifies the database connection is usable."""
    await session.execute(text("SELECT 1"))
    return ReadinessResponse(status="ok", database="connected")
