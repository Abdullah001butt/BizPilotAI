"""Stock movement model — the append-only audit trail of inventory changes."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CompanyOwnedMixin, IdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.product import Product


class StockMovementReason(str, Enum):
    """Why a stock level changed."""

    SALE = "sale"
    PURCHASE = "purchase"
    ADJUSTMENT = "adjustment"
    RETURN = "return"


class StockMovement(IdMixin, CompanyOwnedMixin, TimestampMixin, Base):
    """A single change to a product's on-hand quantity."""

    __tablename__ = "stock_movements"

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Signed delta: positive = stock in, negative = stock out.
    change: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[StockMovementReason] = mapped_column(
        SAEnum(StockMovementReason, native_enum=False, length=20), nullable=False
    )
    reference: Mapped[str | None] = mapped_column(String(60), nullable=True)

    product: Mapped[Product] = relationship(back_populates="movements")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<StockMovement product_id={self.product_id} change={self.change}>"
