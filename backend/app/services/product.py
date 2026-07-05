"""Product & inventory business logic (tenant-scoped)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.product import Product
from app.models.stock_movement import StockMovement, StockMovementReason
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate, StockAdjust


class InsufficientStockError(BusinessRuleError):
    error_code = "insufficient_stock"
    message = "Not enough stock to complete this operation."


class ProductService:
    """CRUD + stock adjustments for a company's products."""

    def __init__(self, session: AsyncSession, company_id: int) -> None:
        self.session = session
        self.company_id = company_id
        self.products = ProductRepository(session, company_id)

    async def list(self) -> list[Product]:
        return await self.products.list(limit=500)

    async def low_stock(self) -> list[Product]:
        return await self.products.list_low_stock()

    async def get(self, product_id: int) -> Product:
        product = await self.products.get(product_id)
        if product is None:
            raise NotFoundError("Product not found.")
        return product

    async def create(self, data: ProductCreate) -> Product:
        if await self.products.get_by_sku(data.sku):
            raise ConflictError("A product with this SKU already exists.")

        payload = data.model_dump()
        quantity = payload.pop("quantity", 0)
        product = Product(company_id=self.company_id, quantity=quantity, **payload)
        await self.products.add(product)

        # Record the opening balance as a movement, for a complete audit trail.
        if quantity:
            self.session.add(
                StockMovement(
                    company_id=self.company_id,
                    product_id=product.id,
                    change=quantity,
                    balance_after=quantity,
                    reason=StockMovementReason.ADJUSTMENT,
                    reference="opening balance",
                )
            )
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def update(self, product_id: int, data: ProductUpdate) -> Product:
        product = await self.get(product_id)
        payload = data.model_dump(exclude_unset=True)

        new_sku = payload.get("sku")
        if new_sku and new_sku != product.sku and await self.products.get_by_sku(new_sku):
            raise ConflictError("A product with this SKU already exists.")

        for field, value in payload.items():
            setattr(product, field, value)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def delete(self, product_id: int) -> None:
        product = await self.get(product_id)
        await self.products.delete(product)
        await self.session.commit()

    async def adjust_stock(self, product_id: int, data: StockAdjust) -> Product:
        product = await self.get(product_id)
        new_quantity = product.quantity + data.change
        if new_quantity < 0:
            raise InsufficientStockError()

        product.quantity = new_quantity
        self.session.add(
            StockMovement(
                company_id=self.company_id,
                product_id=product.id,
                change=data.change,
                balance_after=new_quantity,
                reason=data.reason,
                reference=data.reference,
            )
        )
        await self.session.commit()
        await self.session.refresh(product)
        return product
