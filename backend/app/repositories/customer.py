"""Customer data-access repository (tenant-scoped)."""

from __future__ import annotations

from app.models.customer import Customer
from app.repositories.base import TenantScopedRepository


class CustomerRepository(TenantScopedRepository[Customer]):
    """Queries scoped to a single company's customers."""

    model = Customer
