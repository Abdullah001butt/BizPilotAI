"""End-to-end tests for the authentication flow."""

from __future__ import annotations

from httpx import AsyncClient

from app.core.config import settings

PREFIX = settings.API_V1_PREFIX

VALID_USER = {
    "email": "jane@bizpilot.ai",
    "full_name": "Jane Doe",
    "company_name": "Acme Inc",
    "password": "Secret123",
}


async def _register(client: AsyncClient, **overrides) -> dict:
    payload = {**VALID_USER, **overrides}
    return await client.post(f"{PREFIX}/auth/register", json=payload)


async def _login(client: AsyncClient, email: str, password: str) -> dict:
    return await client.post(
        f"{PREFIX}/auth/login", json={"email": email, "password": password}
    )


# ── Registration ─────────────────────────────────────────────────────────────
async def test_register_creates_company_owner_admin(client: AsyncClient) -> None:
    response = await _register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == VALID_USER["email"]
    # The first user of a new company is its owner → ADMIN.
    assert body["role"] == "admin"
    assert body["company_id"] >= 1
    assert body["is_active"] is True
    assert "hashed_password" not in body  # never leak the hash


async def test_register_duplicate_email_conflicts(client: AsyncClient) -> None:
    await _register(client)
    response = await _register(client)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


async def test_register_rejects_weak_password(client: AsyncClient) -> None:
    response = await _register(client, password="allletters")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


# ── Login ─────────────────────────────────────────────────────────────────────
async def test_login_returns_token_pair(client: AsyncClient) -> None:
    await _register(client)
    response = await _login(client, VALID_USER["email"], VALID_USER["password"])
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]


async def test_login_wrong_password_unauthorized(client: AsyncClient) -> None:
    await _register(client)
    response = await _login(client, VALID_USER["email"], "WrongPass1")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_failed"


# ── Protected route (/me) ──────────────────────────────────────────────────────
async def test_me_requires_authentication(client: AsyncClient) -> None:
    response = await client.get(f"{PREFIX}/auth/me")
    assert response.status_code == 401


async def test_me_returns_profile_with_token(client: AsyncClient) -> None:
    await _register(client)
    tokens = (await _login(client, VALID_USER["email"], VALID_USER["password"])).json()
    response = await client.get(
        f"{PREFIX}/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == VALID_USER["email"]
    assert body["company"]["name"] == VALID_USER["company_name"]


# ── Refresh rotation + logout ───────────────────────────────────────────────────
async def test_refresh_rotates_and_invalidates_old_token(client: AsyncClient) -> None:
    await _register(client)
    tokens = (await _login(client, VALID_USER["email"], VALID_USER["password"])).json()
    old_refresh = tokens["refresh_token"]

    # First refresh succeeds and returns a new pair.
    refreshed = await client.post(
        f"{PREFIX}/auth/refresh", json={"refresh_token": old_refresh}
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["refresh_token"] != old_refresh

    # Re-using the rotated-out token must now fail.
    replay = await client.post(
        f"{PREFIX}/auth/refresh", json={"refresh_token": old_refresh}
    )
    assert replay.status_code == 401


async def test_logout_revokes_refresh_token(client: AsyncClient) -> None:
    await _register(client)
    tokens = (await _login(client, VALID_USER["email"], VALID_USER["password"])).json()

    logout = await client.post(
        f"{PREFIX}/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert logout.status_code == 204

    after = await client.post(
        f"{PREFIX}/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert after.status_code == 401
