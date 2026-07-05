"""Dashboard analytics schemas. All monetary values are integer minor units (cents)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DashboardKpis(BaseModel):
    revenue_total: int
    revenue_this_month: int
    profit_this_month: int
    sales_count: int
    sales_today_count: int
    sales_today_amount: int


class InventorySummary(BaseModel):
    product_count: int
    low_stock_count: int
    stock_value: int  # sum(quantity * cost_price) in cents


class TrendPoint(BaseModel):
    month: str  # e.g. "Jan"
    revenue: int
    profit: int


class TopProduct(BaseModel):
    product_id: int
    name: str
    units_sold: int
    revenue: int


class RecentSale(BaseModel):
    id: int
    reference: str
    customer_name: str | None
    total: int
    created_at: datetime


class DashboardResponse(BaseModel):
    kpis: DashboardKpis
    inventory: InventorySummary
    customers_count: int
    health_score: int
    health_label: str
    revenue_trend: list[TrendPoint]
    top_products: list[TopProduct]
    recent_sales: list[RecentSale]
