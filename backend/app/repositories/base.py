"""Generic async repository (Repository pattern).

The repository is the *only* layer that talks to SQLAlchemy. Services depend on
repositories, never on the ORM directly, which keeps business logic free of query
details and makes data access uniformly testable. Concrete repositories subclass
this and set `model`.

Note: repositories `flush` (to surface integrity errors and populate ids) but do
not `commit`. Transaction boundaries belong to the service layer.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Reusable CRUD operations shared by all concrete repositories."""

    model: type[ModelType]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, entity_id: int) -> ModelType | None:
        """Fetch a single row by primary key, or `None`."""
        return await self.session.get(self.model, entity_id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[ModelType]:
        """Return a page of rows ordered by primary key."""
        result = await self.session.execute(
            select(self.model).order_by(self.model.id).limit(limit).offset(offset)  # type: ignore[attr-defined]
        )
        return list(result.scalars().all())

    async def add(self, entity: ModelType) -> ModelType:
        """Stage a new entity and flush so its generated id is available."""
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def delete(self, entity: ModelType) -> None:
        """Stage a row for deletion."""
        await self.session.delete(entity)
        await self.session.flush()
