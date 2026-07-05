"""Billing business logic (Stripe subscriptions).

Stripe's SDK is synchronous, so blocking calls are run in a threadpool to avoid
stalling the event loop. All Stripe state is mirrored into the local
`subscriptions` table so the app never has to call Stripe just to check a plan.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import stripe
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.exceptions import BillingUnavailableError, BusinessRuleError
from app.core.logging import get_logger
from app.models.company import Company
from app.models.subscription import PlanTier, Subscription
from app.repositories.subscription import SubscriptionRepository

logger = get_logger(__name__)

_ACTIVE_STATUSES = {"active", "trialing"}


def _configure_stripe() -> None:
    if not settings.is_billing_configured:
        raise BillingUnavailableError()
    stripe.api_key = settings.STRIPE_SECRET_KEY


def _to_datetime(unix_ts: int | None) -> datetime | None:
    return datetime.fromtimestamp(unix_ts, tz=timezone.utc) if unix_ts else None


def _period_end(stripe_sub: Any) -> datetime | None:
    """Extract current_period_end, whether at the top level or on the first item.

    Newer Stripe API versions moved this field onto subscription items.
    """
    ts = stripe_sub.get("current_period_end")
    if ts is None:
        try:
            ts = stripe_sub["items"]["data"][0]["current_period_end"]
        except (KeyError, IndexError, TypeError):
            ts = None
    return _to_datetime(ts)


class BillingService:
    def __init__(self, session: AsyncSession, company: Company) -> None:
        self.session = session
        self.company = company
        self.subs = SubscriptionRepository(session)

    async def get_or_create_subscription(self) -> Subscription:
        """Return the company's subscription, creating a FREE one if absent."""
        sub = await self.subs.get_by_company(self.company.id)
        if sub is None:
            sub = Subscription(company_id=self.company.id, plan=PlanTier.FREE, status="free")
            await self.subs.add(sub)
            await self.session.commit()
            await self.session.refresh(sub)
        return sub

    async def create_checkout_session(self) -> str:
        """Create a Stripe Checkout session to upgrade to Pro; return its URL."""
        _configure_stripe()
        sub = await self.get_or_create_subscription()
        customer_id = sub.stripe_customer_id or await self._create_customer(sub)

        session = await run_in_threadpool(
            stripe.checkout.Session.create,
            mode="subscription",
            customer=customer_id,
            line_items=[{"price": settings.STRIPE_PRICE_ID, "quantity": 1}],
            success_url=f"{settings.FRONTEND_URL}/settings?billing=success",
            cancel_url=f"{settings.FRONTEND_URL}/settings?billing=cancelled",
            metadata={"company_id": str(self.company.id)},
        )
        return session.url

    async def create_portal_session(self) -> str:
        """Create a Stripe Customer Portal session; return its URL."""
        _configure_stripe()
        sub = await self.get_or_create_subscription()
        if not sub.stripe_customer_id:
            raise BusinessRuleError("No billing account yet — upgrade to Pro first.")

        session = await run_in_threadpool(
            stripe.billing_portal.Session.create,
            customer=sub.stripe_customer_id,
            return_url=f"{settings.FRONTEND_URL}/settings",
        )
        return session.url

    async def sync_from_stripe(self) -> Subscription:
        """Pull the customer's current subscription state from Stripe.

        Used as a fallback so upgrades reflect immediately after Checkout even
        without a configured webhook (webhooks remain the real-time path).
        """
        sub = await self.get_or_create_subscription()
        if not settings.is_billing_configured or not sub.stripe_customer_id:
            return sub
        _configure_stripe()

        stripe_subs = await run_in_threadpool(
            stripe.Subscription.list,
            customer=sub.stripe_customer_id,
            status="all",
            limit=10,
        )
        active = next((s for s in stripe_subs.data if s.status in _ACTIVE_STATUSES), None)
        if active is not None:
            sub.plan = PlanTier.PRO
            sub.status = active.status
            sub.stripe_subscription_id = active.id
            sub.current_period_end = _period_end(active)
        else:
            sub.plan = PlanTier.FREE
            if stripe_subs.data:
                sub.status = stripe_subs.data[0].status
        await self.session.commit()
        await self.session.refresh(sub)
        return sub

    async def _create_customer(self, sub: Subscription) -> str:
        customer = await run_in_threadpool(
            stripe.Customer.create,
            name=self.company.name,
            metadata={"company_id": str(self.company.id)},
        )
        sub.stripe_customer_id = customer.id
        await self.session.commit()
        return customer.id


class StripeWebhookHandler:
    """Applies Stripe webhook events to local subscription state."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.subs = SubscriptionRepository(session)

    async def handle(self, event: dict[str, Any]) -> None:
        event_type = event.get("type", "")
        obj = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            await self._activate(obj.get("customer"), obj.get("subscription"))
        elif event_type in {"customer.subscription.created", "customer.subscription.updated"}:
            await self._sync_subscription(obj)
        elif event_type == "customer.subscription.deleted":
            await self._downgrade(obj.get("customer"))
        else:
            logger.info("stripe_webhook_ignored", type=event_type)

    async def _activate(self, customer_id: str | None, subscription_id: str | None) -> None:
        sub = await self._find(customer_id)
        if sub is None:
            return
        sub.plan = PlanTier.PRO
        sub.status = "active"
        sub.stripe_subscription_id = subscription_id
        await self.session.commit()
        logger.info("subscription_activated", company_id=sub.company_id)

    async def _sync_subscription(self, obj: dict[str, Any]) -> None:
        sub = await self._find(obj.get("customer"))
        if sub is None:
            return
        status = obj.get("status", "active")
        sub.status = status
        sub.plan = PlanTier.PRO if status in _ACTIVE_STATUSES else PlanTier.FREE
        sub.stripe_subscription_id = obj.get("id")
        sub.current_period_end = _period_end(obj)
        await self.session.commit()
        logger.info("subscription_synced", company_id=sub.company_id, status=status)

    async def _downgrade(self, customer_id: str | None) -> None:
        sub = await self._find(customer_id)
        if sub is None:
            return
        sub.plan = PlanTier.FREE
        sub.status = "canceled"
        await self.session.commit()
        logger.info("subscription_canceled", company_id=sub.company_id)

    async def _find(self, customer_id: str | None) -> Subscription | None:
        if not customer_id:
            return None
        return await self.subs.get_by_customer(customer_id)
