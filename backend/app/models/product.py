"""Product model (company-scoped).

Monetary fields are stored as **integer minor units** (e.g. cents) — never
floats — to eliminate rounding errors in pricing and accounting.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CompanyOwnedMixin, IdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.stock_movement import StockMovement
    from app.models.supplier import Supplier


class Product(IdMixin, CompanyOwnedMixin, TimestampMixin, Base):
    """A sellable/stockable item in a company's inventory."""

    __tablename__ = "products"
    # SKU is unique per company, not globally.
    __table_args__ = (UniqueConstraint("company_id", "sku", name="uq_products_company_id_sku"),)

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    sku: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Money in minor units (cents).
    unit_price: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # selling
    cost_price: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # purchase

    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reorder_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    supplier: Mapped[Supplier | None] = relationship(back_populates="products")
    movements: Mapped[list[StockMovement]] = relationship(
        back_populates="product", cascade="all, delete-orphan", passive_deletes=True
    )

    @property
    def is_low_stock(self) -> bool:
        return self.quantity <= self.reorder_level

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Product id={self.id} sku={self.sku!r} qty={self.quantity}>"
