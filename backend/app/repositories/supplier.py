"""Supplier data-access repository (tenant-scoped)."""

from __future__ import annotations

from app.models.supplier import Supplier
from app.repositories.base import TenantScopedRepository


class SupplierRepository(TenantScopedRepository[Supplier]):
    """Queries scoped to a single company's suppliers."""

    model = Supplier
