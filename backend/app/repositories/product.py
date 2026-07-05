"""Product data-access repository (tenant-scoped)."""

from __future__ import annotations

from sqlalchemy import func, select

from app.models.product import Product
from app.repositories.base import TenantScopedRepository


class ProductRepository(TenantScopedRepository[Product]):
    """Queries scoped to a single company's products."""

    model = Product

    async def get_by_sku(self, sku: str) -> Product | None:
        result = await self.session.execute(
            select(Product).where(
                Product.company_id == self.company_id, Product.sku == sku
            )
        )
        return result.scalar_one_or_none()

    async def list_low_stock(self) -> list[Product]:
        """Active products at or below their reorder level."""
        result = await self.session.execute(
            select(Product)
            .where(
                Product.company_id == self.company_id,
                Product.is_active.is_(True),
                Product.quantity <= Product.reorder_level,
            )
            .order_by(Product.quantity)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Product).where(
                Product.company_id == self.company_id
            )
        )
        return int(result.scalar_one() or 0)
