"""API key model — programmatic, company-scoped access tokens.

Only a SHA-256 hash of each key is stored. The full key is shown to the user
exactly once, at creation. A short, non-secret `prefix` is stored in the clear so
keys can be listed and identified in the UI without revealing the secret.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import IdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company


class ApiKey(IdMixin, TimestampMixin, Base):
    """A hashed API key belonging to a company."""

    __tablename__ = "api_keys"

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    # Human-recognisable, non-secret prefix (e.g. "bp_live_a1b2c3d4").
    prefix: Mapped[str] = mapped_column(String(24), index=True, nullable=False)
    hashed_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    company: Mapped[Company] = relationship(back_populates="api_keys")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<ApiKey id={self.id} company_id={self.company_id} prefix={self.prefix!r}>"
