"""Pytest fixtures.

Each test runs against a fresh in-memory SQLite database with the real schema,
fully isolated. We override the `get_db` dependency so the app uses the test
session, and exercise the app through an in-process ASGI transport (no network).
"""

from __future__ import annotations

import os

# Configure the environment BEFORE importing anything that builds Settings.
os.environ.setdefault("SECRET_KEY", "test-secret-key-test-secret-key-0123456789")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("BACKEND_CORS_ORIGINS", "http://localhost:5173")
# Force external integrations OFF in tests so the suite never makes a live call
# and gating behaves predictably — a local .env may hold real keys, which
# pydantic-settings would otherwise read.
os.environ["GEMINI_API_KEY"] = ""
os.environ["STRIPE_SECRET_KEY"] = ""
os.environ["STRIPE_PRICE_ID"] = ""
os.environ["STRIPE_WEBHOOK_SECRET"] = ""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (register models on the metadata)
from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest_asyncio.fixture
async def db_engine():
    """A fresh in-memory database with all tables created, per test."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # one shared connection keeps the in-memory DB alive
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_engine) -> AsyncClient:
    """An httpx client wired to the app, using the test database session."""
    test_session_factory = async_sessionmaker(
        bind=db_engine, expire_on_commit=False, autoflush=False
    )

    async def _override_get_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
