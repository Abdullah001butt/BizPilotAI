"""Refresh-token data-access repository."""

from __future__ import annotations

from sqlalchemy import select, update

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Queries scoped to the `refresh_tokens` table."""

    model = RefreshToken

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Fetch a stored refresh token by its hashed jti."""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke_all_for_user(self, user_id: int) -> None:
        """Revoke every active session for a user (e.g. global logout)."""
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
            .values(revoked=True)
        )
        await self.session.flush()
