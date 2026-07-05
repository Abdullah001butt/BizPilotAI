"""Supplier business logic (tenant-scoped CRUD)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.supplier import Supplier
from app.repositories.supplier import SupplierRepository
from app.schemas.supplier import SupplierCreate, SupplierUpdate


class SupplierService:
    def __init__(self, session: AsyncSession, company_id: int) -> None:
        self.session = session
        self.company_id = company_id
        self.suppliers = SupplierRepository(session, company_id)

    async def list(self) -> list[Supplier]:
        return await self.suppliers.list(limit=500)

    async def get(self, supplier_id: int) -> Supplier:
        supplier = await self.suppliers.get(supplier_id)
        if supplier is None:
            raise NotFoundError("Supplier not found.")
        return supplier

    async def create(self, data: SupplierCreate) -> Supplier:
        supplier = Supplier(company_id=self.company_id, **data.model_dump())
        await self.suppliers.add(supplier)
        await self.session.commit()
        await self.session.refresh(supplier)
        return supplier

    async def update(self, supplier_id: int, data: SupplierUpdate) -> Supplier:
        supplier = await self.get(supplier_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(supplier, field, value)
        await self.session.commit()
        await self.session.refresh(supplier)
        return supplier

    async def delete(self, supplier_id: int) -> None:
        supplier = await self.get(supplier_id)
        await self.suppliers.delete(supplier)
        await self.session.commit()
