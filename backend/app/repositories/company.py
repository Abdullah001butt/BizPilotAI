"""Company data-access repository."""

from __future__ import annotations

from sqlalchemy import func, select

from app.models.company import Company
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    """Queries scoped to the `companies` table."""

    model = Company

    async def slug_exists(self, slug: str) -> bool:
        """Return whether a company already uses this slug."""
        result = await self.session.execute(
            select(func.count()).select_from(Company).where(Company.slug == slug)
        )
        return (result.scalar_one() or 0) > 0
