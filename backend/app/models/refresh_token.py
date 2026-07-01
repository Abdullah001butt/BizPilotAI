"""Refresh-token model — enables session revocation and token rotation.

We persist only a SHA-256 hash of each refresh token's `jti`, never the token
itself. On refresh we look the row up, verify it is neither revoked nor expired,
revoke it, and issue a fresh pair (rotation). On logout we revoke it.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import IdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(IdMixin, TimestampMixin, Base):
    """A single issued refresh token (one row per active session)."""

    __tablename__ = "refresh_tokens"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # SHA-256 hex digest of the token's jti — unique, indexed for fast lookup.
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<RefreshToken id={self.id} user_id={self.user_id} revoked={self.revoked}>"
