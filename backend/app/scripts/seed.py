"""Idempotent seed script — creates the first company and its admin user.

Run after migrations:  `python -m app.scripts.seed`
Credentials come from FIRST_SUPERUSER_* settings.
"""

from __future__ import annotations

import asyncio

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.services.company import CompanyService

logger = get_logger(__name__)


async def seed_admin() -> None:
    """Create the configured company + superuser if they do not already exist."""
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        if await repo.email_exists(settings.FIRST_SUPERUSER_EMAIL):
            logger.info("seed_skipped", reason="admin already exists")
            return

        company = await CompanyService(session).create("BizPilot HQ")
        admin = User(
            company_id=company.id,
            email=settings.FIRST_SUPERUSER_EMAIL.lower(),
            full_name=settings.FIRST_SUPERUSER_NAME,
            hashed_password=hash_password(settings.FIRST_SUPERUSER_PASSWORD),
            role=UserRole.ADMIN,
            is_superuser=True,
            is_active=True,
        )
        await repo.add(admin)
        await session.commit()
        logger.info("seed_admin_created", email=admin.email, company_id=company.id)


def main() -> None:
    configure_logging()
    asyncio.run(seed_admin())


if __name__ == "__main__":
    main()
