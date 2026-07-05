"""User-facing schemas. `UserPublic` never exposes the password hash."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole
from app.schemas.company import CompanyPublic

_HAS_LETTER = re.compile(r"[A-Za-z]")
_HAS_DIGIT = re.compile(r"\d")


class UserPublic(BaseModel):
    """The safe, public representation of a user returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    is_superuser: bool
    created_at: datetime


class MeResponse(BaseModel):
    """The authenticated user together with their company context."""

    user: UserPublic
    company: CompanyPublic


class ProfileUpdate(BaseModel):
    """Update the current user's own profile."""

    full_name: str = Field(min_length=2, max_length=120)

    @field_validator("full_name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Full name cannot be blank.")
        return cleaned


class PasswordChange(BaseModel):
    """Change the current user's password."""

    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _password_strength(cls, value: str) -> str:
        if not _HAS_LETTER.search(value) or not _HAS_DIGIT.search(value):
            raise ValueError("Password must contain at least one letter and one digit.")
        return value
