"""Supplier model (company-scoped)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CompanyOwnedMixin, IdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.product import Product


class Supplier(IdMixin, CompanyOwnedMixin, TimestampMixin, Base):
    """A vendor a company purchases stock from."""

    __tablename__ = "suppliers"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    products: Mapped[list[Product]] = relationship(back_populates="supplier")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Supplier id={self.id} name={self.name!r}>"
