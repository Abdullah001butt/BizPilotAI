"""Token schemas returned by the auth endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class TokenPair(BaseModel):
    """An access/refresh token pair returned on login and refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT claims (used internally / for typing)."""

    sub: str
    type: str
    exp: int
    iat: int
    role: str | None = None
    jti: str | None = None
