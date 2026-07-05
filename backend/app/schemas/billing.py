"""Billing / subscription schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.subscription import PlanTier


class SubscriptionPublic(BaseModel):
    """The company's current plan and billing status."""

    model_config = ConfigDict(from_attributes=True)

    plan: PlanTier
    status: str
    is_pro: bool
    current_period_end: datetime | None


class BillingConfig(BaseModel):
    """Whether billing is enabled on this deployment (for the frontend)."""

    configured: bool
    publishable_key: str | None = None


class CheckoutResponse(BaseModel):
    """A Stripe-hosted URL to redirect the browser to."""

    url: str
