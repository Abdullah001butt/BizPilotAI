"""Builds a compact, live snapshot of a company's business for the Copilot.

The snapshot is injected into the system prompt so the model answers grounded in
the tenant's real data instead of guessing. It is always scoped to one company.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.customer import Customer
from app.models.sale import Sale, SaleStatus
from app.repositories.product import ProductRepository
from app.services.analytics import AnalyticsService


async def build_business_context(session: AsyncSession, company: Company) -> str:
    """Return a concise, human-readable summary of the company's current state."""
    currency = company.currency

    def money(cents: int) -> str:
        return f"{cents / 100:.2f} {currency}"

    dash = await AnalyticsService(session, company.id).get_dashboard()
    k, inv = dash.kpis, dash.inventory

    lines: list[str] = [
        f"Company: {company.name} (reporting currency: {currency})",
        f"Revenue — this month: {money(k.revenue_this_month)}, all-time: {money(k.revenue_total)}",
        f"Profit this month: {money(k.profit_this_month)}",
        f"Sales — today: {k.sales_today_count} ({money(k.sales_today_amount)}), "
        f"all-time count: {k.sales_count}",
        f"Business health score: {dash.health_score}/100 ({dash.health_label})",
        f"Inventory — products: {inv.product_count}, low-stock: {inv.low_stock_count}, "
        f"stock value: {money(inv.stock_value)}",
        f"Customers on file: {dash.customers_count}",
    ]

    if dash.top_products:
        lines.append(
            "Top products by revenue: "
            + "; ".join(
                f"{p.name} ({p.units_sold} sold, {money(p.revenue)})" for p in dash.top_products
            )
        )

    low = await ProductRepository(session, company.id).list_low_stock()
    if low:
        lines.append(
            "Items to reorder: "
            + "; ".join(
                f"{p.name} (qty {p.quantity}, reorder at {p.reorder_level})" for p in low[:10]
            )
        )

    top_customers = await _top_customers(session, company.id, money)
    if top_customers:
        lines.append("Top customers by spend: " + top_customers)

    return "\n".join(lines)


async def _top_customers(session: AsyncSession, company_id: int, money) -> str:
    result = await session.execute(
        select(Customer.name, func.sum(Sale.total))
        .join(Sale, Sale.customer_id == Customer.id)
        .where(Sale.company_id == company_id, Sale.status == SaleStatus.COMPLETED)
        .group_by(Customer.id)
        .order_by(func.sum(Sale.total).desc())
        .limit(5)
    )
    rows = result.all()
    return "; ".join(f"{name} ({money(int(total or 0))})" for name, total in rows)
