"""SQLAlchemy declarative base.

A consistent constraint-naming convention is essential: Alembic uses these names
to generate stable migrations, and without it SQLite/Postgres pick differing
auto-names that make autogenerate diffs noisy and `--autogenerate` downgrades fail.
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Deterministic names for indexes, constraints, and keys across all backends.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model in the application."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
