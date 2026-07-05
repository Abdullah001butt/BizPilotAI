"""Company (tenant) settings endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import AdminUser, CompanyServiceDep, CurrentCompany
from app.schemas.company import CompanyPublic, CompanyUpdate

router = APIRouter(prefix="/company", tags=["company"])


@router.get("", response_model=CompanyPublic, summary="Get current company")
async def get_company(company: CurrentCompany) -> CompanyPublic:
    """Return the authenticated user's company profile and settings."""
    return CompanyPublic.model_validate(company)


@router.patch("", response_model=CompanyPublic, summary="Update company settings")
async def update_company(
    data: CompanyUpdate,
    company: CurrentCompany,
    service: CompanyServiceDep,
    _: AdminUser,  # only admins may edit company-wide settings
) -> CompanyPublic:
    """Update company profile / settings. Admin-only."""
    updated = await service.update(company, data)
    return CompanyPublic.model_validate(updated)
