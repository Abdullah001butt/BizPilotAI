"""User-facing schemas. `UserPublic` never exposes the password hash."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole


class UserPublic(BaseModel):
    """The safe, public representation of a user returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    is_superuser: bool
    created_at: datetime
