"""Reusable model mixins (DRY).

Every table gets a surrogate integer primary key and audit timestamps. Keeping
these in mixins means a new model is a few lines, and the audit behaviour is
guaranteed identical across the whole schema.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class IdMixin:
    """Surrogate auto-incrementing integer primary key."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class CompanyOwnedMixin:
    """Adds the tenant foreign key shared by every company-owned table (DRY).

    Pairing this with `TenantScopedRepository` guarantees consistent multi-tenant
    isolation across the whole business schema.
    """

    @declared_attr
    def company_id(cls) -> Mapped[int]:  # noqa: N805
        return mapped_column(
            ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
        )


class TimestampMixin:
    """`created_at` / `updated_at` audit columns, maintained by the database."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
