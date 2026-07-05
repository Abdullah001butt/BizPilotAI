"""Security primitives: password hashing and JWT creation/verification.

This module is intentionally pure — it has no database or FastAPI dependencies,
so it is fast and easy to unit-test in isolation.

Token strategy
--------------
* **Access token**  — short-lived (minutes), carries the user id + role, sent on
  every request. Stateless: never stored server-side.
* **Refresh token** — long-lived (days), carries a unique `jti`. We store only a
  *hash* of the jti server-side, which lets us revoke sessions (logout) and
  rotate tokens on every refresh.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import AuthenticationError

# Argon2id — OWASP-recommended, memory-hard, no 72-byte truncation like bcrypt.
_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

TokenType = Literal["access", "refresh"]


# ─────────────────────────────── Passwords ──────────────────────────────────
def hash_password(password: str) -> str:
    """Return an Argon2 hash of the given plaintext password."""
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Constant-time verification of a plaintext password against its hash."""
    return _pwd_context.verify(plain_password, hashed_password)


# ──────────────────────────────── JWT core ──────────────────────────────────
def _create_token(
    *,
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(*, subject: str, role: str, company_id: int) -> str:
    """Create a short-lived access token carrying the user's role and tenant."""
    return _create_token(
        subject=subject,
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims={"role": role, "cid": company_id},
    )


def create_refresh_token(*, subject: str, jti: str) -> str:
    """Create a long-lived refresh token identified by a unique `jti`."""
    return _create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        extra_claims={"jti": jti},
    )


def decode_token(token: str, *, expected_type: TokenType) -> dict[str, Any]:
    """Decode and validate a JWT, enforcing its expected type.

    Raises:
        AuthenticationError: if the token is malformed, expired, or the wrong type.
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Token has expired.") from exc
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Could not validate credentials.") from exc

    if payload.get("type") != expected_type:
        raise AuthenticationError("Invalid token type.")
    return payload


def hash_token_id(jti: str) -> str:
    """Hash a refresh-token `jti` for at-rest storage.

    We store only this hash, so a database leak never exposes usable tokens.
    SHA-256 is sufficient here because the jti is already a high-entropy UUID.
    """
    return hashlib.sha256(jti.encode("utf-8")).hexdigest()
