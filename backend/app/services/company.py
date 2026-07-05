"""Company (tenant) business logic."""

from __future__ import annotations

import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import slugify
from app.models.company import Company
from app.repositories.company import CompanyRepository
from app.schemas.company import CompanyUpdate


class CompanyService:
    """Create and manage company records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.companies = CompanyRepository(session)

    async def create(self, name: str) -> Company:
        """Create a company with a unique slug. Does not commit (caller owns tx)."""
        slug = await self._unique_slug(name)
        company = Company(name=name.strip(), slug=slug, preferences={})
        await self.companies.add(company)
        return company

    async def update(self, company: Company, data: CompanyUpdate) -> Company:
        """Apply a partial update to a company and commit."""
        payload = data.model_dump(exclude_unset=True)
        for field, value in payload.items():
            setattr(company, field, value)
        await self.session.commit()
        await self.session.refresh(company)
        return company

    async def _unique_slug(self, name: str) -> str:
        base = slugify(name)
        slug = base
        while await self.companies.slug_exists(slug):
            slug = f"{base}-{secrets.token_hex(3)}"
        return slug
