"""Reusable FastAPI dependencies: DB session, services, and auth guards.

These are the composition root for dependency injection. Routes declare *what*
they need (`CurrentUser`, `AdminUser`, `AuthServiceDep`) and FastAPI wires it up.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, NotFoundError, PermissionDeniedError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.company import Company
from app.models.user import User, UserRole
from app.repositories.company import CompanyRepository
from app.repositories.user import UserRepository
from app.services.api_key import ApiKeyService
from app.services.auth import AuthService
from app.services.company import CompanyService
from app.services.user import UserService

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


# ── Tenant context ────────────────────────────────────────────────────────────
async def get_current_company(session: SessionDep, user: CurrentUser) -> Company:
    """Load the company (tenant) the authenticated user belongs to."""
    company = await CompanyRepository(session).get(user.company_id)
    if company is None:
        raise NotFoundError("Company not found.")
    return company


CurrentCompany = Annotated[Company, Depends(get_current_company)]


# ── Service factories ─────────────────────────────────────────────────────────
def get_company_service(session: SessionDep) -> CompanyService:
    return CompanyService(session)


def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)


def get_api_key_service(session: SessionDep, user: CurrentUser) -> ApiKeyService:
    """An API-key service already scoped to the caller's tenant."""
    return ApiKeyService(session, user.company_id)


CompanyServiceDep = Annotated[CompanyService, Depends(get_company_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
ApiKeyServiceDep = Annotated[ApiKeyService, Depends(get_api_key_service)]
