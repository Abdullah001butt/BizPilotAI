"""Reusable FastAPI dependencies: DB session, services, and auth guards.

These are the composition root for dependency injection. Routes declare *what*
they need (`CurrentUser`, `AdminUser`, `AuthServiceDep`) and FastAPI wires it up.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import LLMProvider
from app.ai.gemini import GeminiProvider
from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    NotFoundError,
    PaymentRequiredError,
    PermissionDeniedError,
)
from app.core.security import decode_token
from app.db.session import get_db
from app.models.company import Company
from app.models.user import User, UserRole
from app.repositories.company import CompanyRepository
from app.repositories.user import UserRepository
from app.services.analytics import AnalyticsService
from app.services.api_key import ApiKeyService
from app.services.auth import AuthService
from app.services.billing import BillingService
from app.services.company import CompanyService
from app.services.copilot import CopilotService
from app.services.customer import CustomerService
from app.services.product import ProductService
from app.services.sale import SaleService
from app.services.supplier import SupplierService
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


# ── Tenant-scoped business services ───────────────────────────────────────────
def get_product_service(session: SessionDep, user: CurrentUser) -> ProductService:
    return ProductService(session, user.company_id)


def get_supplier_service(session: SessionDep, user: CurrentUser) -> SupplierService:
    return SupplierService(session, user.company_id)


def get_customer_service(session: SessionDep, user: CurrentUser) -> CustomerService:
    return CustomerService(session, user.company_id)


def get_sale_service(session: SessionDep, user: CurrentUser) -> SaleService:
    return SaleService(session, user.company_id)


def get_analytics_service(session: SessionDep, user: CurrentUser) -> AnalyticsService:
    return AnalyticsService(session, user.company_id)


ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
SupplierServiceDep = Annotated[SupplierService, Depends(get_supplier_service)]
CustomerServiceDep = Annotated[CustomerService, Depends(get_customer_service)]
SaleServiceDep = Annotated[SaleService, Depends(get_sale_service)]
AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]


# ── AI Copilot ────────────────────────────────────────────────────────────────
@lru_cache
def _build_provider() -> LLMProvider | None:
    """Build the LLM provider once per process (None if no API key is set)."""
    if not settings.is_ai_configured:
        return None
    return GeminiProvider(settings.GEMINI_API_KEY, settings.GEMINI_MODEL)


def get_llm_provider() -> LLMProvider | None:
    return _build_provider()


def get_copilot_service(
    session: SessionDep,
    company: CurrentCompany,
    provider: Annotated[LLMProvider | None, Depends(get_llm_provider)],
) -> CopilotService:
    return CopilotService(session, company, provider)


CopilotServiceDep = Annotated[CopilotService, Depends(get_copilot_service)]


# ── Billing ───────────────────────────────────────────────────────────────────
def get_billing_service(session: SessionDep, company: CurrentCompany) -> BillingService:
    return BillingService(session, company)


BillingServiceDep = Annotated[BillingService, Depends(get_billing_service)]


async def require_pro(session: SessionDep, company: CurrentCompany) -> None:
    """Gate a route behind a Pro subscription.

    Gating is only enforced when billing is actually configured, so a deployment
    without Stripe keys (e.g. local dev) keeps every feature open.
    """
    if not settings.is_billing_configured:
        return
    subscription = await BillingService(session, company).get_or_create_subscription()
    if not subscription.is_pro:
        raise PaymentRequiredError("The AI Copilot is available on the Pro plan.")


RequirePro = Annotated[None, Depends(require_pro)]
