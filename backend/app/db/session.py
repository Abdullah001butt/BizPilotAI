"""Async database engine, session factory, and the FastAPI session dependency."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


def _build_engine() -> AsyncEngine:
    """Create the async engine, tuned for the configured database backend."""
    if settings.is_sqlite:
        # SQLite has no real connection pool; `check_same_thread` must be off so
        # the async driver can share the connection across the event loop.
        return create_async_engine(
            settings.DATABASE_URL,
            echo=settings.SQL_ECHO,
            connect_args={"check_same_thread": False},
        )

    # PostgreSQL: a pooled connection with pre-ping to survive idle drops.
    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.SQL_ECHO,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )


engine: AsyncEngine = _build_engine()

# `expire_on_commit=False` keeps ORM objects usable after the request's commit,
# which is what we want when serialising a response after `await session.commit()`.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a database session per request.

    The session is always closed; commits are the explicit responsibility of the
    service layer so business operations control their own transaction boundaries.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
