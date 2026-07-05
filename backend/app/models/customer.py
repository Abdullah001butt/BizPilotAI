"""Customer model (company-scoped).

Intentionally minimal for Phase 4 (Sales). Phase 6 (CRM) extends this with
contacts, insights, and lifetime-value fields — no rework, just more columns.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CompanyOwnedMixin, IdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.sale import Sale


class Customer(IdMixin, CompanyOwnedMixin, TimestampMixin, Base):
    """A person or business a company sells to."""

    __tablename__ = "customers"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    sales: Mapped[list[Sale]] = relationship(back_populates="customer")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Customer id={self.id} name={self.name!r}>"
