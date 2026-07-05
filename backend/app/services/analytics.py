"""Dashboard analytics — live, tenant-scoped business metrics.

Aggregation is done in Python over a bounded result set (the company's completed
sales + products) rather than DB-specific date SQL, so it behaves identically on
SQLite and PostgreSQL. All money is integer minor units (cents).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.product import Product
from app.models.sale import Sale, SaleStatus
from app.schemas.dashboard import (
    DashboardKpis,
    DashboardResponse,
    InventorySummary,
    RecentSale,
    TopProduct,
    TrendPoint,
)

_MONTH_ABBR = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def _naive(dt: datetime) -> datetime:
    """Drop tzinfo so SQLite (naive) and Postgres (aware) compare consistently."""
    return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


class AnalyticsService:
    def __init__(self, session: AsyncSession, company_id: int) -> None:
        self.session = session
        self.company_id = company_id

    async def get_dashboard(self) -> DashboardResponse:
        now = _naive(datetime.now(timezone.utc))
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        today = now.date()

        sales = await self._completed_sales()
        products = await self._products()
        cost_by_product = {p.id: p.cost_price for p in products}
        name_by_product = {p.id: p.name for p in products}

        # Last six month buckets (oldest → newest), keyed by (year, month).
        base = now.year * 12 + (now.month - 1)
        month_keys = [divmod(base - i, 12) for i in range(5, -1, -1)]
        trend: dict[tuple[int, int], list[int]] = {(y, m + 1): [0, 0] for y, m in month_keys}

        revenue_total = revenue_month = cogs_month = 0
        sales_today_count = sales_today_amount = sales_month_count = 0
        top: dict[int, list[int]] = {}

        for sale in sales:
            created = _naive(sale.created_at)
            revenue_total += sale.total
            cogs = sum(i.quantity * cost_by_product.get(i.product_id or -1, 0) for i in sale.items)
            profit = sale.total - cogs

            if created >= month_start:
                revenue_month += sale.total
                cogs_month += cogs
                sales_month_count += 1
            if created.date() == today:
                sales_today_count += 1
                sales_today_amount += sale.total

            key = (created.year, created.month)
            if key in trend:
                trend[key][0] += sale.total
                trend[key][1] += profit

            for item in sale.items:
                if item.product_id is not None:
                    bucket = top.setdefault(item.product_id, [0, 0])
                    bucket[0] += item.quantity
                    bucket[1] += item.line_total

        profit_month = revenue_month - cogs_month

        inventory = InventorySummary(
            product_count=len(products),
            low_stock_count=sum(
                1 for p in products if p.is_active and p.quantity <= p.reorder_level
            ),
            stock_value=sum(p.quantity * p.cost_price for p in products),
        )

        health = self._health_score(
            revenue_month=revenue_month,
            profit_month=profit_month,
            product_count=inventory.product_count,
            low_stock=inventory.low_stock_count,
            sales_month_count=sales_month_count,
        )

        return DashboardResponse(
            kpis=DashboardKpis(
                revenue_total=revenue_total,
                revenue_this_month=revenue_month,
                profit_this_month=profit_month,
                sales_count=len(sales),
                sales_today_count=sales_today_count,
                sales_today_amount=sales_today_amount,
            ),
            inventory=inventory,
            customers_count=await self._customers_count(),
            health_score=health[0],
            health_label=health[1],
            revenue_trend=[
                TrendPoint(
                    month=_MONTH_ABBR[month0],
                    revenue=trend[(year, month0 + 1)][0],
                    profit=trend[(year, month0 + 1)][1],
                )
                for (year, month0) in month_keys
            ],
            top_products=self._top_products(top, name_by_product),
            recent_sales=[
                RecentSale(
                    id=s.id,
                    reference=s.reference,
                    customer_name=s.customer.name if s.customer else None,
                    total=s.total,
                    created_at=s.created_at,
                )
                for s in sales[:5]
            ],
        )

    # ── queries ───────────────────────────────────────────────────────────────
    async def _completed_sales(self) -> list[Sale]:
        result = await self.session.execute(
            select(Sale)
            .where(Sale.company_id == self.company_id, Sale.status == SaleStatus.COMPLETED)
            .options(selectinload(Sale.items), selectinload(Sale.customer))
            .order_by(Sale.created_at.desc(), Sale.id.desc())
        )
        return list(result.scalars().all())

    async def _products(self) -> list[Product]:
        result = await self.session.execute(
            select(Product).where(Product.company_id == self.company_id)
        )
        return list(result.scalars().all())

    async def _customers_count(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Customer).where(
                Customer.company_id == self.company_id
            )
        )
        return int(result.scalar_one() or 0)

    # ── helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _top_products(
        top: dict[int, list[int]], names: dict[int, str]
    ) -> list[TopProduct]:
        ranked = sorted(top.items(), key=lambda kv: kv[1][1], reverse=True)[:5]
        return [
            TopProduct(
                product_id=pid,
                name=names.get(pid, "Deleted product"),
                units_sold=units,
                revenue=revenue,
            )
            for pid, (units, revenue) in ranked
        ]

    @staticmethod
    def _health_score(
        *,
        revenue_month: int,
        profit_month: int,
        product_count: int,
        low_stock: int,
        sales_month_count: int,
    ) -> tuple[int, str]:
        """Composite 0–100 score from margin, stock health, and sales activity."""
        margin = (profit_month / revenue_month) if revenue_month > 0 else 0.0
        margin_score = _clamp01(margin / 0.4)  # 40%+ margin scores full marks
        stock_score = 1.0 - (low_stock / product_count) if product_count else 1.0
        activity_score = _clamp01(sales_month_count / 10)

        score = round(100 * (0.4 * margin_score + 0.3 * stock_score + 0.3 * activity_score))
        if score >= 80:
            label = "Excellent"
        elif score >= 60:
            label = "Healthy"
        elif score >= 40:
            label = "Fair"
        else:
            label = "Needs attention"
        return score, label
