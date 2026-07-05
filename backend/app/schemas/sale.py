"""Sale schemas. Monetary fields are integer minor units (cents)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.sale import SaleStatus
from app.schemas.customer import CustomerBrief


class SaleItemInput(BaseModel):
    """A requested line item. `unit_price` defaults to the product's price."""

    product_id: int
    quantity: int = Field(ge=1)
    unit_price: int | None = Field(default=None, ge=0, description="Override price (cents).")


class SaleCreate(BaseModel):
    customer_id: int | None = None
    items: list[SaleItemInput] = Field(min_length=1)
    discount: int = Field(default=0, ge=0, description="Discount in cents.")
    tax: int = Field(default=0, ge=0, description="Tax in cents.")
    reference: str | None = Field(default=None, max_length=40)
    status: SaleStatus = SaleStatus.COMPLETED
    notes: str | None = None


class SaleItemPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int | None
    description: str
    quantity: int
    unit_price: int
    line_total: int


class SalePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference: str
    customer_id: int | None
    customer: CustomerBrief | None
    status: SaleStatus
    subtotal: int
    discount: int
    tax: int
    total: int
    notes: str | None
    created_at: datetime
    items: list[SaleItemPublic]
