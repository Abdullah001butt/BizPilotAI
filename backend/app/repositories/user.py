"""User data-access repository."""

from __future__ import annotations

from sqlalchemy import func, select

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Queries scoped to the `users` table."""

    model = User

    async def get_by_email(self, email: str) -> User | None:
        """Look a user up by email (case-insensitive)."""
        result = await self.session.execute(
            select(User).where(func.lower(User.email) == email.lower())
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Return whether an account with this email already exists."""
        result = await self.session.execute(
            select(func.count())
            .select_from(User)
            .where(func.lower(User.email) == email.lower())
        )
        return (result.scalar_one() or 0) > 0
