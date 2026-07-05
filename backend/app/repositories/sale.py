"""Sale data-access repository (tenant-scoped).

Reads eagerly load `items` and `customer` so responses can be serialised without
triggering lazy loads (which are unsafe under async SQLAlchemy).
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.sale import Sale
from app.repositories.base import TenantScopedRepository


class SaleRepository(TenantScopedRepository[Sale]):
    """Queries scoped to a single company's sales."""

    model = Sale

    _eager = (selectinload(Sale.items), selectinload(Sale.customer))

    async def get(self, entity_id: int) -> Sale | None:
        result = await self.session.execute(
            select(Sale)
            .where(Sale.id == entity_id, Sale.company_id == self.company_id)
            .options(*self._eager)
        )
        return result.scalar_one_or_none()

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Sale]:
        result = await self.session.execute(
            select(Sale)
            .where(Sale.company_id == self.company_id)
            .options(*self._eager)
            .order_by(Sale.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Sale).where(Sale.company_id == self.company_id)
        )
        return int(result.scalar_one() or 0)

    async def reference_exists(self, reference: str) -> bool:
        result = await self.session.execute(
            select(func.count())
            .select_from(Sale)
            .where(Sale.company_id == self.company_id, Sale.reference == reference)
        )
        return (result.scalar_one() or 0) > 0
