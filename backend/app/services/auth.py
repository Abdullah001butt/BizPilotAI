"""Authentication business logic.

`AuthService` orchestrates repositories + security primitives and owns the
transaction boundary (it commits). API routes stay thin: they validate input,
call a service method, and serialise the result.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    InactiveUserError,
)
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token_id,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.token import TokenPair
from app.services.company import CompanyService

logger = get_logger(__name__)


def _as_aware_utc(value: datetime) -> datetime:
    """Normalise a datetime to timezone-aware UTC.

    SQLite returns naive datetimes while PostgreSQL returns aware ones; treating
    a naive value as UTC lets comparisons work identically across both backends.
    """
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


class AuthService:
    """Coordinates registration, login, token refresh, and logout."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.tokens = RefreshTokenRepository(session)
        self.companies = CompanyService(session)

    # ── Registration ─────────────────────────────────────────────────────────
    async def register(self, data: RegisterRequest) -> User:
        """Register a new company and its owner (an ADMIN) atomically.

        Self-service signup always creates a brand-new tenant; the registrant is
        that company's first administrator. Both rows commit in one transaction,
        so a duplicate-email failure leaves no orphaned company behind.
        """
        if await self.users.email_exists(data.email):
            raise ConflictError("An account with this email already exists.")

        company = await self.companies.create(data.company_name)
        user = User(
            company_id=company.id,
            email=data.email.lower(),
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=UserRole.ADMIN,
        )
        await self.users.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        logger.info(
            "user_registered", user_id=user.id, email=user.email, company_id=company.id
        )
        return user

    # ── Login ─────────────────────────────────────────────────────────────────
    async def authenticate(self, data: LoginRequest) -> User:
        """Verify credentials and return the user, or raise."""
        user = await self.users.get_by_email(data.email)
        # Always run a hash verification to keep timing uniform whether or not the
        # email exists, mitigating user-enumeration via response timing.
        password_ok = verify_password(
            data.password,
            user.hashed_password if user else _DUMMY_HASH,
        )
        if user is None or not password_ok:
            raise AuthenticationError("Incorrect email or password.")
        if not user.is_active:
            raise InactiveUserError()
        return user

    async def login(self, data: LoginRequest) -> tuple[User, TokenPair]:
        """Authenticate and issue a fresh access/refresh token pair."""
        user = await self.authenticate(data)
        tokens = await self._issue_token_pair(user)
        await self.session.commit()
        logger.info("user_login", user_id=user.id)
        return user, tokens

    # ── Refresh (with rotation) ────────────────────────────────────────────────
    async def refresh(self, refresh_token: str) -> TokenPair:
        """Validate a refresh token, rotate it, and return a new pair."""
        payload = decode_token(refresh_token, expected_type="refresh")
        jti = payload.get("jti")
        subject = payload.get("sub")
        if not jti or not subject:
            raise AuthenticationError("Malformed refresh token.")

        stored = await self.tokens.get_by_hash(hash_token_id(jti))
        if stored is None or stored.revoked:
            raise AuthenticationError("Refresh token is no longer valid.")
        if _as_aware_utc(stored.expires_at) < datetime.now(timezone.utc):
            raise AuthenticationError("Refresh token has expired.")

        user = await self.users.get(int(subject))
        if user is None or not user.is_active:
            raise AuthenticationError("Account is unavailable.")

        # Rotation: revoke the presented token, issue a brand-new pair.
        stored.revoked = True
        tokens = await self._issue_token_pair(user)
        await self.session.commit()
        logger.info("token_refreshed", user_id=user.id)
        return tokens

    # ── Logout ──────────────────────────────────────────────────────────────--
    async def logout(self, refresh_token: str) -> None:
        """Revoke the presented refresh token (idempotent / best-effort)."""
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except AuthenticationError:
            return  # Already invalid — nothing to revoke.

        jti = payload.get("jti")
        if not jti:
            return
        stored = await self.tokens.get_by_hash(hash_token_id(jti))
        if stored and not stored.revoked:
            stored.revoked = True
            await self.session.commit()
            logger.info("user_logout", user_id=stored.user_id)

    # ── Internal helpers ───────────────────────────────────────────────────────
    async def _issue_token_pair(self, user: User) -> TokenPair:
        """Mint an access token and a persisted, rotatable refresh token."""
        jti = uuid.uuid4().hex
        access = create_access_token(
            subject=str(user.id), role=user.role.value, company_id=user.company_id
        )
        refresh = create_refresh_token(subject=str(user.id), jti=jti)

        await self.tokens.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_token_id(jti),
                expires_at=datetime.now(timezone.utc)
                + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            )
        )
        return TokenPair(access_token=access, refresh_token=refresh)


# A valid Argon2 hash of a random value, used only to equalise authentication
# timing when the email does not exist. Never matches a real password.
_DUMMY_HASH = hash_password(uuid.uuid4().hex)
