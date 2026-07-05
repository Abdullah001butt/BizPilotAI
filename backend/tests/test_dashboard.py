"""Tests for the live dashboard analytics endpoint."""

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


async def test_dashboard_empty_state(client: AsyncClient) -> None:
    headers = await _signup(client, "empty@x.com", "Empty Co")
    res = await client.get(f"{PREFIX}/dashboard", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["kpis"]["revenue_total"] == 0
    assert body["inventory"]["product_count"] == 0
    assert len(body["revenue_trend"]) == 6  # always six month buckets
    assert body["top_products"] == []


async def test_dashboard_reflects_a_sale(client: AsyncClient) -> None:
    headers = await _signup(client, "dash@x.com", "Dash Co")

    # Product: sells for $10.00, costs $6.00, stock 10.
    product = (
        await client.post(
            f"{PREFIX}/products",
            headers=headers,
            json={
                "name": "Widget",
                "sku": "W1",
                "unit_price": 1000,
                "cost_price": 600,
                "quantity": 10,
                "reorder_level": 2,
            },
        )
    ).json()

    # Sell 4 units → revenue 4000, COGS 2400, profit 1600.
    sale = await client.post(
        f"{PREFIX}/sales",
        headers=headers,
        json={"items": [{"product_id": product["id"], "quantity": 4}]},
    )
    assert sale.status_code == 201

    body = (await client.get(f"{PREFIX}/dashboard", headers=headers)).json()
    assert body["kpis"]["revenue_total"] == 4000
    assert body["kpis"]["revenue_this_month"] == 4000
    assert body["kpis"]["profit_this_month"] == 1600
    assert body["kpis"]["sales_today_count"] == 1
    assert body["inventory"]["product_count"] == 1
    assert body["inventory"]["stock_value"] == 6 * 600  # 6 units left * cost
    assert body["customers_count"] == 0

    # Top products reflect the sale.
    assert body["top_products"][0]["product_id"] == product["id"]
    assert body["top_products"][0]["units_sold"] == 4
    assert body["top_products"][0]["revenue"] == 4000

    # Current month bucket (last in the trend) carries the revenue.
    assert body["revenue_trend"][-1]["revenue"] == 4000
    assert body["health_score"] >= 0
    assert body["recent_sales"][0]["reference"] == "INV-0001"


async def test_dashboard_is_tenant_isolated(client: AsyncClient) -> None:
    headers_a = await _signup(client, "da@x.com", "A Co")
    headers_b = await _signup(client, "db@x.com", "B Co")

    product = (
        await client.post(
            f"{PREFIX}/products",
            headers=headers_a,
            json={"name": "A", "sku": "A1", "unit_price": 500, "quantity": 5},
        )
    ).json()
    await client.post(
        f"{PREFIX}/sales",
        headers=headers_a,
        json={"items": [{"product_id": product["id"], "quantity": 1}]},
    )

    # Tenant B's dashboard sees none of A's activity.
    body_b = (await client.get(f"{PREFIX}/dashboard", headers=headers_b)).json()
    assert body_b["kpis"]["revenue_total"] == 0
    assert body_b["inventory"]["product_count"] == 0
