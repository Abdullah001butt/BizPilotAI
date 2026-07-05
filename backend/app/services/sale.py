"""Sale business logic (tenant-scoped).

Creating a completed sale is a single transaction: it prices each line from the
product (or an override), computes totals, validates stock, decrements inventory,
and writes a stock-movement audit row — all-or-nothing.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.logging import get_logger
from app.models.product import Product
from app.models.sale import Sale, SaleItem, SaleStatus
from app.models.stock_movement import StockMovement, StockMovementReason
from app.repositories.customer import CustomerRepository
from app.repositories.product import ProductRepository
from app.repositories.sale import SaleRepository
from app.schemas.sale import SaleCreate
from app.services.product import InsufficientStockError

logger = get_logger(__name__)


@dataclass
class _LineSpec:
    product: Product
    quantity: int
    unit_price: int
    line_total: int


class SaleService:
    def __init__(self, session: AsyncSession, company_id: int) -> None:
        self.session = session
        self.company_id = company_id
        self.sales = SaleRepository(session, company_id)
        self.products = ProductRepository(session, company_id)
        self.customers = CustomerRepository(session, company_id)

    async def list(self) -> list[Sale]:
        return await self.sales.list(limit=200)

    async def get(self, sale_id: int) -> Sale:
        sale = await self.sales.get(sale_id)
        if sale is None:
            raise NotFoundError("Sale not found.")
        return sale

    async def create(self, data: SaleCreate) -> Sale:
        await self._validate_customer(data.customer_id)
        lines = await self._price_lines(data)
        subtotal = sum(line.line_total for line in lines)
        total = subtotal - data.discount + data.tax
        if total < 0:
            raise BusinessRuleError("Discount cannot exceed the sale total.")

        reference = await self._resolve_reference(data.reference)
        completed = data.status == SaleStatus.COMPLETED

        # For completed sales, ensure every line has enough stock before mutating.
        if completed:
            for line in lines:
                if line.product.quantity < line.quantity:
                    raise InsufficientStockError(
                        f"Insufficient stock for '{line.product.name}' "
                        f"(have {line.product.quantity}, need {line.quantity})."
                    )

        sale = Sale(
            company_id=self.company_id,
            reference=reference,
            customer_id=data.customer_id,
            status=data.status,
            subtotal=subtotal,
            discount=data.discount,
            tax=data.tax,
            total=total,
            notes=data.notes,
        )
        await self.sales.add(sale)

        for line in lines:
            self.session.add(
                SaleItem(
                    sale_id=sale.id,
                    product_id=line.product.id,
                    description=line.product.name,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    line_total=line.line_total,
                )
            )
            if completed:
                line.product.quantity -= line.quantity
                self.session.add(
                    StockMovement(
                        company_id=self.company_id,
                        product_id=line.product.id,
                        change=-line.quantity,
                        balance_after=line.product.quantity,
                        reason=StockMovementReason.SALE,
                        reference=reference,
                    )
                )

        await self.session.commit()
        logger.info("sale_created", sale_id=sale.id, total=total, reference=reference)
        return await self.get(sale.id)

    # ── helpers ────────────────────────────────────────────────────────────────
    async def _validate_customer(self, customer_id: int | None) -> None:
        if customer_id is not None and await self.customers.get(customer_id) is None:
            raise NotFoundError("Customer not found.")

    async def _price_lines(self, data: SaleCreate) -> list[_LineSpec]:
        lines: list[_LineSpec] = []
        for item in data.items:
            product = await self.products.get(item.product_id)
            if product is None:
                raise NotFoundError(f"Product {item.product_id} not found.")
            unit_price = item.unit_price if item.unit_price is not None else product.unit_price
            lines.append(
                _LineSpec(
                    product=product,
                    quantity=item.quantity,
                    unit_price=unit_price,
                    line_total=unit_price * item.quantity,
                )
            )
        return lines

    async def _resolve_reference(self, reference: str | None) -> str:
        if reference:
            if await self.sales.reference_exists(reference):
                raise BusinessRuleError("A sale with this reference already exists.")
            return reference
        # Auto-generate a sequential invoice number, skipping any collisions.
        seq = await self.sales.count() + 1
        candidate = f"INV-{seq:04d}"
        while await self.sales.reference_exists(candidate):
            seq += 1
            candidate = f"INV-{seq:04d}"
        return candidate
