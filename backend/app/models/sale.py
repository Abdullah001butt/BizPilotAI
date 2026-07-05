"""Sale (order/invoice) and its line items (company-scoped).

All monetary fields are integer minor units (cents). A sale's totals are computed
by the service layer from its items; completing a sale decrements product stock.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CompanyOwnedMixin, IdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.customer import Customer


class SaleStatus(str, Enum):
    """Lifecycle of a sale."""

    DRAFT = "draft"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Sale(IdMixin, CompanyOwnedMixin, TimestampMixin, Base):
    """A sales order / invoice."""

    __tablename__ = "sales"
    __table_args__ = (
        UniqueConstraint("company_id", "reference", name="uq_sales_company_id_reference"),
    )

    reference: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[SaleStatus] = mapped_column(
        SAEnum(SaleStatus, native_enum=False, length=20),
        default=SaleStatus.COMPLETED,
        nullable=False,
    )

    # Money in minor units (cents).
    subtotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    discount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tax: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    customer: Mapped[Customer | None] = relationship(back_populates="sales")
    items: Mapped[list[SaleItem]] = relationship(
        back_populates="sale",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Sale id={self.id} ref={self.reference!r} total={self.total}>"


class SaleItem(IdMixin, TimestampMixin, Base):
    """A single line on a sale. Product name/price are snapshotted at sale time."""

    __tablename__ = "sale_items"

    sale_id: Mapped[int] = mapped_column(
        ForeignKey("sales.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Product may later be deleted; keep the line but null the link.
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    description: Mapped[str] = mapped_column(String(160), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)  # cents, snapshot
    line_total: Mapped[int] = mapped_column(Integer, nullable=False)  # cents

    sale: Mapped[Sale] = relationship(back_populates="items")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SaleItem sale_id={self.sale_id} product_id={self.product_id} qty={self.quantity}>"
