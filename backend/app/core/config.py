"""Application configuration.

A single, validated, type-safe `Settings` object is the *only* place the app
reads environment variables. Everything else imports `settings` from here, so
configuration is centralised, validated at startup, and trivial to mock in tests.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Annotated

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Environment(str, Enum):
    """Deployment environments the app can run in."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Strongly-typed application settings loaded from environment / `.env`.

    Validation happens once, at import time, so a misconfigured deployment fails
    fast and loudly instead of breaking deep inside a request.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    PROJECT_NAME: str = "BizPilot AI"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = True

    # ── Security ─────────────────────────────────────────────────────────────
    SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./bizpilot.db"
    SQL_ECHO: bool = False

    # ── CORS ─────────────────────────────────────────────────────────────────
    # `NoDecode` stops pydantic-settings from JSON-decoding the raw env value, so
    # our validator below can accept a plain comma-separated string.
    BACKEND_CORS_ORIGINS: Annotated[list[str], NoDecode] = Field(default_factory=list)

    # ── First admin (used by the seed script) ────────────────────────────────
    FIRST_SUPERUSER_EMAIL: str = "admin@bizpilot.ai"
    FIRST_SUPERUSER_PASSWORD: str = "ChangeMe123!"
    FIRST_SUPERUSER_NAME: str = "BizPilot Admin"

    # ── AI / LLM (Gemini) ────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors(cls, value: object) -> object:
        """Allow CORS origins to be provided as a comma-separated string."""
        if isinstance(value, str) and not value.startswith("["):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == Environment.PRODUCTION

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_ai_configured(self) -> bool:
        return bool(self.GEMINI_API_KEY)


@lru_cache
def get_settings() -> Settings:
    """Return a cached `Settings` instance.

    `lru_cache` guarantees the environment is parsed exactly once per process and
    gives us a single dependency-injection seam for overriding settings in tests.
    """
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
