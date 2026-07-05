"""Subscription model — one billing record per company (tenant)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import IdMixin, TimestampMixin


class PlanTier(str, Enum):
    """Subscription tiers. FREE is the default; PRO unlocks premium features."""

    FREE = "free"
    PRO = "pro"


class Subscription(IdMixin, TimestampMixin, Base):
    """A company's billing state, synced from Stripe."""

    __tablename__ = "subscriptions"

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    plan: Mapped[PlanTier] = mapped_column(
        SAEnum(PlanTier, native_enum=False, length=20),
        default=PlanTier.FREE,
        nullable=False,
    )
    # Free-form status mirroring Stripe (active, trialing, past_due, canceled, …)
    # or "free" for companies that never subscribed.
    status: Mapped[str] = mapped_column(String(30), default="free", nullable=False)

    stripe_customer_id: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    @property
    def is_pro(self) -> bool:
        return self.plan == PlanTier.PRO and self.status in {"active", "trialing"}

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Subscription company_id={self.company_id} "
            f"plan={self.plan.value} status={self.status}>"
        )
