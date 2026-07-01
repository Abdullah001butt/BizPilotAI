"""Reusable FastAPI dependencies: DB session, services, and auth guards.

These are the composition root for dependency injection. Routes declare *what*
they need (`CurrentUser`, `AdminUser`, `AuthServiceDep`) and FastAPI wires it up.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.services.auth import AuthService

# `auto_error=False` lets us raise our own domain error (mapped to a clean 401)
# instead of FastAPI's default 403 when the Authorization header is missing.
_bearer_scheme = HTTPBearer(auto_error=False)

SessionDep = Annotated[AsyncSession, Depends(get_db)]


def get_auth_service(session: SessionDep) -> AuthService:
    """Provide an `AuthService` bound to the request's session."""
    return AuthService(session)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> User:
    """Resolve the authenticated user from a Bearer access token."""
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Not authenticated.")

    payload = decode_token(credentials.credentials, expected_type="access")
    subject = payload.get("sub")
    if subject is None:
        raise AuthenticationError("Invalid authentication token.")

    user = await UserRepository(session).get(int(subject))
    if user is None:
        raise AuthenticationError("User no longer exists.")
    if not user.is_active:
        raise AuthenticationError("Account is inactive.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed: UserRole):
    """Build a dependency that authorises only the given roles.

    Superusers always pass. Usage:  `_: Annotated[User, Depends(require_roles(UserRole.ADMIN))]`
    """

    async def _guard(user: CurrentUser) -> User:
        if user.is_superuser or user.role in allowed:
            return user
        raise PermissionDeniedError()

    return _guard


# Convenience aliases for the common authorisation tiers.
AdminUser = Annotated[User, Depends(require_roles(UserRole.ADMIN))]
ManagerUser = Annotated[User, Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER))]
