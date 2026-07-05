"""Tests for Phase 2: company settings, profile, password, API keys, tenancy."""

from __future__ import annotations

from httpx import AsyncClient

from app.core.config import settings

PREFIX = settings.API_V1_PREFIX


async def _signup(client: AsyncClient, email: str, company: str) -> dict[str, str]:
    """Register a company + owner and return an Authorization header."""
    await client.post(
        f"{PREFIX}/auth/register",
        json={
            "email": email,
            "full_name": "Owner Person",
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


# ── Company settings ───────────────────────────────────────────────────────────
async def test_get_and_update_company(client: AsyncClient) -> None:
    headers = await _signup(client, "a@x.com", "Acme")

    got = await client.get(f"{PREFIX}/company", headers=headers)
    assert got.status_code == 200
    assert got.json()["name"] == "Acme"
    assert got.json()["currency"] == "USD"

    patched = await client.patch(
        f"{PREFIX}/company",
        headers=headers,
        json={"name": "Acme Global", "currency": "eur", "timezone": "Europe/Berlin"},
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["name"] == "Acme Global"
    assert body["currency"] == "EUR"  # normalised to upper-case
    assert body["timezone"] == "Europe/Berlin"


# ── Profile + password ─────────────────────────────────────────────────────────
async def test_update_profile(client: AsyncClient) -> None:
    headers = await _signup(client, "b@x.com", "Bravo")
    res = await client.patch(
        f"{PREFIX}/users/me", headers=headers, json={"full_name": "New Name"}
    )
    assert res.status_code == 200
    assert res.json()["full_name"] == "New Name"


async def test_change_password_then_login_with_new(client: AsyncClient) -> None:
    headers = await _signup(client, "c@x.com", "Charlie")

    changed = await client.post(
        f"{PREFIX}/users/me/password",
        headers=headers,
        json={"current_password": "Secret123", "new_password": "Brand2New"},
    )
    assert changed.status_code == 204

    # Old password rejected, new password works.
    old = await client.post(
        f"{PREFIX}/auth/login", json={"email": "c@x.com", "password": "Secret123"}
    )
    assert old.status_code == 401
    new = await client.post(
        f"{PREFIX}/auth/login", json={"email": "c@x.com", "password": "Brand2New"}
    )
    assert new.status_code == 200


async def test_change_password_wrong_current_rejected(client: AsyncClient) -> None:
    headers = await _signup(client, "d@x.com", "Delta")
    res = await client.post(
        f"{PREFIX}/users/me/password",
        headers=headers,
        json={"current_password": "WrongOne1", "new_password": "Brand2New"},
    )
    assert res.status_code == 401


# ── API keys ───────────────────────────────────────────────────────────────────
async def test_api_key_lifecycle(client: AsyncClient) -> None:
    headers = await _signup(client, "e@x.com", "Echo")

    created = await client.post(
        f"{PREFIX}/api-keys", headers=headers, json={"name": "CI token"}
    )
    assert created.status_code == 201
    body = created.json()
    assert body["key"].startswith("bp_")  # plaintext returned once
    assert body["prefix"].startswith("bp_")
    key_id = body["id"]

    listed = await client.get(f"{PREFIX}/api-keys", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert "key" not in listed.json()[0]  # secret never listed

    revoked = await client.delete(f"{PREFIX}/api-keys/{key_id}", headers=headers)
    assert revoked.status_code == 204
    assert (await client.get(f"{PREFIX}/api-keys", headers=headers)).json()[0]["revoked"] is True


# ── Tenant isolation ───────────────────────────────────────────────────────────
async def test_tenants_cannot_see_each_others_api_keys(client: AsyncClient) -> None:
    tenant_a = await _signup(client, "owner-a@x.com", "Tenant A")
    tenant_b = await _signup(client, "owner-b@x.com", "Tenant B")

    a_key = await client.post(
        f"{PREFIX}/api-keys", headers=tenant_a, json={"name": "A key"}
    )
    a_key_id = a_key.json()["id"]

    # Tenant B must not see Tenant A's key...
    b_list = await client.get(f"{PREFIX}/api-keys", headers=tenant_b)
    assert b_list.json() == []

    # ...nor revoke it (scoped repository returns None → 404).
    cross = await client.delete(f"{PREFIX}/api-keys/{a_key_id}", headers=tenant_b)
    assert cross.status_code == 404
