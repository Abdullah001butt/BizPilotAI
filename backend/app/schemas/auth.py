"""Authentication request schemas with input validation."""

from __future__ import annotations

import re

from pydantic import BaseModel, EmailStr, Field, field_validator

# At least one letter and one digit; length enforced separately for a clear message.
_HAS_LETTER = re.compile(r"[A-Za-z]")
_HAS_DIGIT = re.compile(r"\d")


class RegisterRequest(BaseModel):
    """Payload to create a new account (and its company on first signup)."""

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    company_name: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("company_name")
    @classmethod
    def _strip_company(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Company name cannot be blank.")
        return cleaned

    @field_validator("password")
    @classmethod
    def _password_strength(cls, value: str) -> str:
        if not _HAS_LETTER.search(value) or not _HAS_DIGIT.search(value):
            raise ValueError("Password must contain at least one letter and one digit.")
        return value

    @field_validator("full_name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Full name cannot be blank.")
        return cleaned


class LoginRequest(BaseModel):
    """Payload to authenticate with email + password."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    """Payload to exchange a refresh token for a new token pair."""

    refresh_token: str = Field(min_length=1)
