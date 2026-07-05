"""Tests for billing: plans, gating, and webhook sync (no live Stripe calls)."""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.deps import get_llm_provider
from app.core.config import settings
from app.db.base import Base
from app.main import app
from app.models.company import Company
from app.models.subscription import PlanTier, Subscription
from app.services.billing import StripeWebhookHandler
from tests.test_copilot import FakeProvider

PREFIX = settings.API_V1_PREFIX


async def _signup(client: AsyncClient, email: str, company: str) -> dict[str, str]:
    await client.post(
        f"{PREFIX}/auth/register",
        json={
            "email": email,
            "full_name": "Owner",
            "company_name": company,
            "password": "Secret123",
        },
    )
    tokens = (
        await client.post(
            f"{PREFIX}/auth/login", json={"email": email, "password": "Secret123"}
        )
    ).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


# ── Default plan + config ──────────────────────────────────────────────────────
async def test_new_company_is_free(client: AsyncClient) -> None:
    headers = await _signup(client, "free@x.com", "Free Co")
    res = await client.get(f"{PREFIX}/billing/subscription", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["plan"] == "free"
    assert body["is_pro"] is False


async def test_billing_config_reports_unconfigured(client: AsyncClient) -> None:
    headers = await _signup(client, "cfg@x.com", "Cfg Co")
    res = await client.get(f"{PREFIX}/billing/config", headers=headers)
    assert res.json()["configured"] is False


async def test_checkout_requires_billing_configured(client: AsyncClient) -> None:
    headers = await _signup(client, "co@x.com", "Co Co")
    res = await client.post(f"{PREFIX}/billing/checkout", headers=headers)
    assert res.status_code == 503
    assert res.json()["error"]["code"] == "billing_not_configured"


# ── Copilot gating ─────────────────────────────────────────────────────────────
async def test_copilot_open_when_billing_unconfigured(client: AsyncClient) -> None:
    """With no Stripe keys, the Copilot is NOT gated (dev stays open)."""
    fake = FakeProvider()
    app.dependency_overrides[get_llm_provider] = lambda: fake
    try:
        headers = await _signup(client, "open@x.com", "Open Co")
        res = await client.post(
            f"{PREFIX}/copilot/chat",
            headers=headers,
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
        assert res.status_code == 200
    finally:
        app.dependency_overrides.pop(get_llm_provider, None)


async def test_copilot_gated_for_free_plan_when_billing_configured(
    client: AsyncClient, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_dummy")
    monkeypatch.setattr(settings, "STRIPE_PRICE_ID", "price_dummy")
    fake = FakeProvider()
    app.dependency_overrides[get_llm_provider] = lambda: fake
    try:
        headers = await _signup(client, "gated@x.com", "Gated Co")
        res = await client.post(
            f"{PREFIX}/copilot/chat",
            headers=headers,
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
        assert res.status_code == 402
        assert res.json()["error"]["code"] == "payment_required"
    finally:
        app.dependency_overrides.pop(get_llm_provider, None)


# ── Webhook sync (unit test of the handler) ─────────────────────────────────────
async def test_webhook_activates_and_cancels_pro() -> None:
    engine = create_async_engine(
        "sqlite+aiosqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        company = Company(name="Acme", slug="acme", preferences={})
        session.add(company)
        await session.flush()
        sub = Subscription(
            company_id=company.id, plan=PlanTier.FREE, status="free", stripe_customer_id="cus_1"
        )
        session.add(sub)
        await session.commit()

        handler = StripeWebhookHandler(session)

        # checkout.session.completed → upgrades to Pro.
        await handler.handle(
            {
                "type": "checkout.session.completed",
                "data": {"object": {"customer": "cus_1", "subscription": "sub_1"}},
            }
        )
        await session.refresh(sub)
        assert sub.plan == PlanTier.PRO
        assert sub.is_pro is True

        # subscription canceled → back to Free.
        await handler.handle(
            {
                "type": "customer.subscription.deleted",
                "data": {"object": {"customer": "cus_1"}},
            }
        )
        await session.refresh(sub)
        assert sub.plan == PlanTier.FREE
        assert sub.status == "canceled"

    await engine.dispose()
