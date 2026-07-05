"""API key business logic (tenant-scoped)."""

from __future__ import annotations

import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.core.security import hash_token_id
from app.models.api_key import ApiKey
from app.repositories.api_key import ApiKeyRepository

logger = get_logger(__name__)

_KEY_PREFIX = "bp"  # BizPilot key namespace → keys look like "bp_<secret>"


class ApiKeyService:
    """Issue, list, and revoke a company's API keys."""

    def __init__(self, session: AsyncSession, company_id: int) -> None:
        self.session = session
        self.company_id = company_id
        self.keys = ApiKeyRepository(session, company_id)

    async def list(self) -> list[ApiKey]:
        return await self.keys.list()

    async def create(self, name: str) -> tuple[ApiKey, str]:
        """Create a key and return the ORM row plus the one-time plaintext key."""
        secret = secrets.token_urlsafe(24)
        full_key = f"{_KEY_PREFIX}_{secret}"
        api_key = ApiKey(
            company_id=self.company_id,
            name=name.strip(),
            prefix=full_key[:11],  # "bp_" + 8 chars, safe to display
            hashed_key=hash_token_id(full_key),
        )
        await self.keys.add(api_key)
        await self.session.commit()
        await self.session.refresh(api_key)
        logger.info("api_key_created", company_id=self.company_id, api_key_id=api_key.id)
        return api_key, full_key

    async def revoke(self, api_key_id: int) -> None:
        """Revoke a key owned by the current tenant."""
        api_key = await self.keys.get(api_key_id)
        if api_key is None:
            raise NotFoundError("API key not found.")
        api_key.revoked = True
        await self.session.commit()
        logger.info("api_key_revoked", company_id=self.company_id, api_key_id=api_key_id)
