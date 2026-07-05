"""Sales endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import ManagerUser, SaleServiceDep
from app.schemas.sale import SaleCreate, SalePublic

router = APIRouter(prefix="/sales", tags=["sales"])


@router.get("", response_model=list[SalePublic], summary="List sales")
async def list_sales(service: SaleServiceDep) -> list[SalePublic]:
    return [SalePublic.model_validate(s) for s in await service.list()]


@router.get("/{sale_id}", response_model=SalePublic, summary="Get a sale")
async def get_sale(sale_id: int, service: SaleServiceDep) -> SalePublic:
    return SalePublic.model_validate(await service.get(sale_id))


@router.post(
    "",
    response_model=SalePublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a sale",
)
async def create_sale(
    data: SaleCreate, service: SaleServiceDep, _: ManagerUser
) -> SalePublic:
    """Create a sale. A completed sale decrements product stock atomically."""
    return SalePublic.model_validate(await service.create(data))
