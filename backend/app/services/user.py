"""User self-service business logic (profile + password)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.schemas.user import PasswordChange, ProfileUpdate

logger = get_logger(__name__)


class UserService:
    """Operations a user performs on their own account."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tokens = RefreshTokenRepository(session)

    async def update_profile(self, user: User, data: ProfileUpdate) -> User:
        """Update the user's own profile fields."""
        user.full_name = data.full_name
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def change_password(self, user: User, data: PasswordChange) -> None:
        """Change password after verifying the current one.

        All existing sessions are revoked, forcing re-authentication everywhere —
        the correct behaviour after a credential change.
        """
        if not verify_password(data.current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect.")

        user.hashed_password = hash_password(data.new_password)
        await self.tokens.revoke_all_for_user(user.id)
        await self.session.commit()
        logger.info("password_changed", user_id=user.id)
