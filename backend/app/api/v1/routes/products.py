"""Product & inventory endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.api.deps import ManagerUser, ProductServiceDep
from app.schemas.product import (
    ProductCreate,
    ProductPublic,
    ProductUpdate,
    StockAdjust,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductPublic], summary="List products")
async def list_products(service: ProductServiceDep) -> list[ProductPublic]:
    products = await service.list()
    return [ProductPublic.model_validate(p) for p in products]


@router.get("/low-stock", response_model=list[ProductPublic], summary="Low-stock products")
async def low_stock(service: ProductServiceDep) -> list[ProductPublic]:
    products = await service.low_stock()
    return [ProductPublic.model_validate(p) for p in products]


@router.get("/{product_id}", response_model=ProductPublic, summary="Get a product")
async def get_product(product_id: int, service: ProductServiceDep) -> ProductPublic:
    return ProductPublic.model_validate(await service.get(product_id))


@router.post(
    "",
    response_model=ProductPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product",
)
async def create_product(
    data: ProductCreate, service: ProductServiceDep, _: ManagerUser
) -> ProductPublic:
    return ProductPublic.model_validate(await service.create(data))


@router.patch("/{product_id}", response_model=ProductPublic, summary="Update a product")
async def update_product(
    product_id: int, data: ProductUpdate, service: ProductServiceDep, _: ManagerUser
) -> ProductPublic:
    return ProductPublic.model_validate(await service.update(product_id, data))


@router.post(
    "/{product_id}/stock",
    response_model=ProductPublic,
    summary="Adjust product stock",
)
async def adjust_stock(
    product_id: int, data: StockAdjust, service: ProductServiceDep, _: ManagerUser
) -> ProductPublic:
    return ProductPublic.model_validate(await service.adjust_stock(product_id, data))


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
)
async def delete_product(
    product_id: int, service: ProductServiceDep, _: ManagerUser
) -> Response:
    await service.delete(product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
