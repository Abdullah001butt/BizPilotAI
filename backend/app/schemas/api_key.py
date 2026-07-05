"""API key schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyPublic(BaseModel):
    """Safe representation of an API key — never includes the secret."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    prefix: str
    last_used_at: datetime | None
    revoked: bool
    created_at: datetime


class ApiKeyCreate(BaseModel):
    """Payload to create a new API key."""

    name: str = Field(min_length=1, max_length=80)


class ApiKeyCreated(ApiKeyPublic):
    """Returned exactly once, on creation — carries the plaintext key."""

    key: str
