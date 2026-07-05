"""Small, dependency-free helpers shared across the app."""

from __future__ import annotations

import re

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    """Turn arbitrary text into a URL-safe slug (lowercase, hyphenated)."""
    slug = _SLUG_STRIP.sub("-", value.strip().lower()).strip("-")
    return slug or "company"
