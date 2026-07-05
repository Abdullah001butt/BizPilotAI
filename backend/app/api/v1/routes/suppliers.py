"""Supplier endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.api.deps import ManagerUser, SupplierServiceDep
from app.schemas.supplier import SupplierCreate, SupplierPublic, SupplierUpdate

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierPublic], summary="List suppliers")
async def list_suppliers(service: SupplierServiceDep) -> list[SupplierPublic]:
    return [SupplierPublic.model_validate(s) for s in await service.list()]


@router.get("/{supplier_id}", response_model=SupplierPublic, summary="Get a supplier")
async def get_supplier(supplier_id: int, service: SupplierServiceDep) -> SupplierPublic:
    return SupplierPublic.model_validate(await service.get(supplier_id))


@router.post(
    "",
    response_model=SupplierPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a supplier",
)
async def create_supplier(
    data: SupplierCreate, service: SupplierServiceDep, _: ManagerUser
) -> SupplierPublic:
    return SupplierPublic.model_validate(await service.create(data))


@router.patch("/{supplier_id}", response_model=SupplierPublic, summary="Update a supplier")
async def update_supplier(
    supplier_id: int, data: SupplierUpdate, service: SupplierServiceDep, _: ManagerUser
) -> SupplierPublic:
    return SupplierPublic.model_validate(await service.update(supplier_id, data))


@router.delete(
    "/{supplier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a supplier",
)
async def delete_supplier(
    supplier_id: int, service: SupplierServiceDep, _: ManagerUser
) -> Response:
    await service.delete(supplier_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
