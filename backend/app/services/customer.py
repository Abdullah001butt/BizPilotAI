"""Customer business logic (tenant-scoped CRUD)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.customer import Customer
from app.repositories.customer import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerService:
    def __init__(self, session: AsyncSession, company_id: int) -> None:
        self.session = session
        self.company_id = company_id
        self.customers = CustomerRepository(session, company_id)

    async def list(self) -> list[Customer]:
        return await self.customers.list(limit=500)

    async def get(self, customer_id: int) -> Customer:
        customer = await self.customers.get(customer_id)
        if customer is None:
            raise NotFoundError("Customer not found.")
        return customer

    async def create(self, data: CustomerCreate) -> Customer:
        customer = Customer(company_id=self.company_id, **data.model_dump())
        await self.customers.add(customer)
        await self.session.commit()
        await self.session.refresh(customer)
        return customer

    async def update(self, customer_id: int, data: CustomerUpdate) -> Customer:
        customer = await self.get(customer_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(customer, field, value)
        await self.session.commit()
        await self.session.refresh(customer)
        return customer

    async def delete(self, customer_id: int) -> None:
        customer = await self.get(customer_id)
        await self.customers.delete(customer)
        await self.session.commit()
