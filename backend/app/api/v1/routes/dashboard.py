"""Dashboard analytics endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import AnalyticsServiceDep
from app.schemas.dashboard import DashboardResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse, summary="Live business metrics")
async def get_dashboard(service: AnalyticsServiceDep) -> DashboardResponse:
    """Aggregated KPIs, trends, top products, and health score for the tenant."""
    return await service.get_dashboard()
