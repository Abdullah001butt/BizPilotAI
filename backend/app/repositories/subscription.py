"""Subscription data-access repository."""

from __future__ import annotations

from sqlalchemy import select

from app.models.subscription import Subscription
from app.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    """Queries over the `subscriptions` table (one row per company)."""

    model = Subscription

    async def get_by_company(self, company_id: int) -> Subscription | None:
        result = await self.session.execute(
            select(Subscription).where(Subscription.company_id == company_id)
        )
        return result.scalar_one_or_none()

    async def get_by_customer(self, stripe_customer_id: str) -> Subscription | None:
        result = await self.session.execute(
            select(Subscription).where(
                Subscription.stripe_customer_id == stripe_customer_id
            )
        )
        return result.scalar_one_or_none()
