"""API key data-access repository (tenant-scoped)."""

from __future__ import annotations

from sqlalchemy import select

from app.models.api_key import ApiKey
from app.repositories.base import TenantScopedRepository


class ApiKeyRepository(TenantScopedRepository[ApiKey]):
    """Queries scoped to a single company's API keys."""

    model = ApiKey

    async def get_by_hash(self, hashed_key: str) -> ApiKey | None:
        """Look up an API key by its hash (used for programmatic auth).

        Not tenant-filtered: the hash itself identifies the owning company.
        """
        result = await self.session.execute(
            select(ApiKey).where(ApiKey.hashed_key == hashed_key)
        )
        return result.scalar_one_or_none()
