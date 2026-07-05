"""Customer endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.api.deps import CustomerServiceDep, ManagerUser
from app.schemas.customer import CustomerCreate, CustomerPublic, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[CustomerPublic], summary="List customers")
async def list_customers(service: CustomerServiceDep) -> list[CustomerPublic]:
    return [CustomerPublic.model_validate(c) for c in await service.list()]


@router.get("/{customer_id}", response_model=CustomerPublic, summary="Get a customer")
async def get_customer(customer_id: int, service: CustomerServiceDep) -> CustomerPublic:
    return CustomerPublic.model_validate(await service.get(customer_id))


@router.post(
    "",
    response_model=CustomerPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a customer",
)
async def create_customer(
    data: CustomerCreate, service: CustomerServiceDep, _: ManagerUser
) -> CustomerPublic:
    return CustomerPublic.model_validate(await service.create(data))


@router.patch("/{customer_id}", response_model=CustomerPublic, summary="Update a customer")
async def update_customer(
    customer_id: int, data: CustomerUpdate, service: CustomerServiceDep, _: ManagerUser
) -> CustomerPublic:
    return CustomerPublic.model_validate(await service.update(customer_id, data))


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a customer",
)
async def delete_customer(
    customer_id: int, service: CustomerServiceDep, _: ManagerUser
) -> Response:
    await service.delete(customer_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
