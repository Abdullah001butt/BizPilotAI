"""Billing endpoints: subscription status, Stripe Checkout, Portal, and webhook."""

from __future__ import annotations

import stripe
from fastapi import APIRouter, Header, Request, Response, status

from app.api.deps import AdminUser, BillingServiceDep, SessionDep
from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.billing import BillingConfig, CheckoutResponse, SubscriptionPublic
from app.services.billing import StripeWebhookHandler

logger = get_logger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/config", response_model=BillingConfig, summary="Billing availability")
async def billing_config() -> BillingConfig:
    """Report whether billing is enabled (used by the frontend to show upgrades)."""
    return BillingConfig(
        configured=settings.is_billing_configured,
        publishable_key=settings.STRIPE_PUBLISHABLE_KEY or None,
    )


@router.get("/subscription", response_model=SubscriptionPublic, summary="Current plan")
async def get_subscription(service: BillingServiceDep) -> SubscriptionPublic:
    """Return the company's current plan and billing status."""
    subscription = await service.get_or_create_subscription()
    return SubscriptionPublic.model_validate(subscription)


@router.post("/checkout", response_model=CheckoutResponse, summary="Upgrade to Pro")
async def create_checkout(service: BillingServiceDep, _: AdminUser) -> CheckoutResponse:
    """Create a Stripe Checkout session and return its URL. Admin-only."""
    return CheckoutResponse(url=await service.create_checkout_session())


@router.post("/portal", response_model=CheckoutResponse, summary="Manage billing")
async def create_portal(service: BillingServiceDep, _: AdminUser) -> CheckoutResponse:
    """Create a Stripe Customer Portal session and return its URL. Admin-only."""
    return CheckoutResponse(url=await service.create_portal_session())


@router.post("/sync", response_model=SubscriptionPublic, summary="Sync plan from Stripe")
async def sync_subscription(service: BillingServiceDep) -> SubscriptionPublic:
    """Refresh the local plan from Stripe (used on return from Checkout)."""
    subscription = await service.sync_from_stripe()
    return SubscriptionPublic.model_validate(subscription)


@router.post("/webhook", include_in_schema=False, summary="Stripe webhook")
async def stripe_webhook(
    request: Request,
    session: SessionDep,
    stripe_signature: str = Header(default="", alias="Stripe-Signature"),
) -> Response:
    """Receive Stripe events and sync subscription state. Signature-verified."""
    if not settings.STRIPE_WEBHOOK_SECRET:
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.SignatureVerificationError):
        logger.warning("stripe_webhook_bad_signature")
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    await StripeWebhookHandler(session).handle(event)
    return Response(status_code=status.HTTP_200_OK)
