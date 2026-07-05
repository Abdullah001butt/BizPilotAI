"""Tests for Phase 4: inventory (products) and sales with stock decrement."""

from __future__ import annotations

from httpx import AsyncClient

from app.core.config import settings

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


async def _create_product(client: AsyncClient, headers: dict[str, str], **overrides) -> dict:
    payload = {
        "name": "Widget",
        "sku": "WGT-1",
        "unit_price": 1000,  # $10.00 in cents
        "cost_price": 600,
        "quantity": 10,
        "reorder_level": 3,
        **overrides,
    }
    return (await client.post(f"{PREFIX}/products", headers=headers, json=payload)).json()


# ── Products CRUD ──────────────────────────────────────────────────────────────
async def test_product_crud(client: AsyncClient) -> None:
    headers = await _signup(client, "p@x.com", "P Co")

    created = await client.post(
        f"{PREFIX}/products",
        headers=headers,
        json={"name": "Widget", "sku": "WGT-1", "unit_price": 1000, "quantity": 5},
    )
    assert created.status_code == 201
    pid = created.json()["id"]
    assert created.json()["quantity"] == 5
    assert created.json()["is_low_stock"] is False

    listed = await client.get(f"{PREFIX}/products", headers=headers)
    assert len(listed.json()) == 1

    updated = await client.patch(
        f"{PREFIX}/products/{pid}", headers=headers, json={"unit_price": 1500}
    )
    assert updated.json()["unit_price"] == 1500

    deleted = await client.delete(f"{PREFIX}/products/{pid}", headers=headers)
    assert deleted.status_code == 204
    assert (await client.get(f"{PREFIX}/products", headers=headers)).json() == []


async def test_duplicate_sku_conflicts(client: AsyncClient) -> None:
    headers = await _signup(client, "p2@x.com", "P2 Co")
    await _create_product(client, headers)
    dupe = await client.post(
        f"{PREFIX}/products",
        headers=headers,
        json={"name": "Other", "sku": "WGT-1", "unit_price": 500},
    )
    assert dupe.status_code == 409


# ── Stock adjustments ──────────────────────────────────────────────────────────
async def test_stock_adjust_and_low_stock(client: AsyncClient) -> None:
    headers = await _signup(client, "s@x.com", "S Co")
    product = await _create_product(client, headers, quantity=5, reorder_level=3)
    pid = product["id"]

    lowered = await client.post(
        f"{PREFIX}/products/{pid}/stock",
        headers=headers,
        json={"change": -3, "reason": "adjustment"},
    )
    assert lowered.status_code == 200
    assert lowered.json()["quantity"] == 2
    assert lowered.json()["is_low_stock"] is True

    low = await client.get(f"{PREFIX}/products/low-stock", headers=headers)
    assert len(low.json()) == 1

    # Cannot go below zero.
    too_much = await client.post(
        f"{PREFIX}/products/{pid}/stock", headers=headers, json={"change": -100}
    )
    assert too_much.status_code == 422
    assert too_much.json()["error"]["code"] == "insufficient_stock"


# ── Sales ──────────────────────────────────────────────────────────────────────
async def test_sale_decrements_stock_and_totals(client: AsyncClient) -> None:
    headers = await _signup(client, "sale@x.com", "Sale Co")
    product = await _create_product(client, headers, quantity=10, unit_price=1000)
    pid = product["id"]

    sale = await client.post(
        f"{PREFIX}/sales",
        headers=headers,
        json={"items": [{"product_id": pid, "quantity": 3}], "tax": 150},
    )
    assert sale.status_code == 201
    body = sale.json()
    assert body["reference"] == "INV-0001"
    assert body["subtotal"] == 3000
    assert body["total"] == 3150  # subtotal - discount + tax
    assert body["items"][0]["line_total"] == 3000

    # Stock decremented from 10 → 7.
    refreshed = await client.get(f"{PREFIX}/products/{pid}", headers=headers)
    assert refreshed.json()["quantity"] == 7


async def test_sale_insufficient_stock_rejected(client: AsyncClient) -> None:
    headers = await _signup(client, "sale2@x.com", "Sale2 Co")
    product = await _create_product(client, headers, quantity=2)
    res = await client.post(
        f"{PREFIX}/sales",
        headers=headers,
        json={"items": [{"product_id": product["id"], "quantity": 5}]},
    )
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "insufficient_stock"


# ── Tenant isolation ───────────────────────────────────────────────────────────
async def test_products_are_tenant_isolated(client: AsyncClient) -> None:
    tenant_a = await _signup(client, "a-inv@x.com", "Tenant A")
    tenant_b = await _signup(client, "b-inv@x.com", "Tenant B")

    product_a = await _create_product(client, tenant_a, sku="A-SKU")

    # B sees no products and cannot sell A's product.
    assert (await client.get(f"{PREFIX}/products", headers=tenant_b)).json() == []
    cross_sale = await client.post(
        f"{PREFIX}/sales",
        headers=tenant_b,
        json={"items": [{"product_id": product_a["id"], "quantity": 1}]},
    )
    assert cross_sale.status_code == 404
