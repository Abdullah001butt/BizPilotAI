"""Company (tenant) schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CompanyPublic(BaseModel):
    """Public representation of a company."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    industry: str | None
    currency: str
    timezone: str
    fiscal_year_start_month: int
    phone: str | None
    address: str | None
    logo_url: str | None
    preferences: dict[str, Any]
    created_at: datetime


class CompanyUpdate(BaseModel):
    """Partial update of company profile / settings (all fields optional)."""

    name: str | None = Field(default=None, min_length=2, max_length=160)
    industry: str | None = Field(default=None, max_length=80)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    timezone: str | None = Field(default=None, max_length=64)
    fiscal_year_start_month: int | None = Field(default=None, ge=1, le=12)
    phone: str | None = Field(default=None, max_length=40)
    address: str | None = Field(default=None, max_length=255)
    logo_url: str | None = Field(default=None, max_length=500)
    preferences: dict[str, Any] | None = None

    @field_validator("currency")
    @classmethod
    def _upper_currency(cls, value: str | None) -> str | None:
        return value.upper() if value else value
