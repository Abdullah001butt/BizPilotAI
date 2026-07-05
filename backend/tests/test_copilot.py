"""Tests for the AI Copilot (using a fake provider — no live LLM calls)."""

from __future__ import annotations

from httpx import AsyncClient

from app.ai.base import Turn
from app.api.deps import get_llm_provider
from app.core.config import settings
from app.main import app

PREFIX = settings.API_V1_PREFIX


class FakeProvider:
    """Records the system prompt and echoes the last user turn."""

    def __init__(self) -> None:
        self.last_system: str | None = None

    async def generate(self, *, system: str, history: list[Turn]) -> str:
        self.last_system = system
        return "FAKE: " + history[-1].text


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


async def test_status_reports_unconfigured_without_key(client: AsyncClient) -> None:
    headers = await _signup(client, "ai1@x.com", "AI Co")
    res = await client.get(f"{PREFIX}/copilot/status", headers=headers)
    assert res.status_code == 200
    assert res.json()["configured"] is False


async def test_chat_returns_503_when_not_configured(client: AsyncClient) -> None:
    headers = await _signup(client, "ai2@x.com", "AI2 Co")
    res = await client.post(
        f"{PREFIX}/copilot/chat",
        headers=headers,
        json={"messages": [{"role": "user", "content": "Hi"}]},
    )
    assert res.status_code == 503
    assert res.json()["error"]["code"] == "ai_not_configured"


async def test_chat_grounds_answer_in_live_data(client: AsyncClient) -> None:
    fake = FakeProvider()
    app.dependency_overrides[get_llm_provider] = lambda: fake
    try:
        headers = await _signup(client, "ai3@x.com", "Acme Traders")
        # Seed some data so the context is non-trivial.
        product = (
            await client.post(
                f"{PREFIX}/products",
                headers=headers,
                json={"name": "Gizmo", "sku": "G1", "unit_price": 2000, "quantity": 5},
            )
        ).json()
        await client.post(
            f"{PREFIX}/sales",
            headers=headers,
            json={"items": [{"product_id": product["id"], "quantity": 2}]},
        )

        res = await client.post(
            f"{PREFIX}/copilot/chat",
            headers=headers,
            json={"messages": [{"role": "user", "content": "What is my revenue?"}]},
        )
        assert res.status_code == 200
        assert res.json()["message"].startswith("FAKE: What is my revenue?")

        # The system prompt must carry the tenant's live business context.
        assert fake.last_system is not None
        assert "Acme Traders" in fake.last_system
        assert "LIVE BUSINESS DATA" in fake.last_system
        assert "Gizmo" in fake.last_system
    finally:
        app.dependency_overrides.pop(get_llm_provider, None)
