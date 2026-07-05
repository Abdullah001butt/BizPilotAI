"""Product schemas. Monetary fields are integer minor units (cents)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.stock_movement import StockMovementReason


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    sku: str = Field(min_length=1, max_length=60)
    description: str | None = None
    category: str | None = Field(default=None, max_length=80)
    barcode: str | None = Field(default=None, max_length=64)
    unit_price: int = Field(ge=0, description="Selling price in minor units (cents).")
    cost_price: int = Field(default=0, ge=0, description="Cost in minor units (cents).")
    reorder_level: int = Field(default=0, ge=0)
    supplier_id: int | None = None
    is_active: bool = True


class ProductCreate(ProductBase):
    quantity: int = Field(default=0, ge=0, description="Initial stock on hand.")


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    sku: str | None = Field(default=None, min_length=1, max_length=60)
    description: str | None = None
    category: str | None = Field(default=None, max_length=80)
    barcode: str | None = Field(default=None, max_length=64)
    unit_price: int | None = Field(default=None, ge=0)
    cost_price: int | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    supplier_id: int | None = None
    is_active: bool | None = None


class ProductPublic(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quantity: int
    is_low_stock: bool
    created_at: datetime


class StockAdjust(BaseModel):
    """Adjust a product's stock by a signed delta."""

    change: int = Field(description="Signed quantity delta (+ in, - out).")
    reason: StockMovementReason = StockMovementReason.ADJUSTMENT
    reference: str | None = Field(default=None, max_length=60)
