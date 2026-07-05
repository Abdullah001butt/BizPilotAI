"""Provider-agnostic LLM interface.

Keeping this abstraction lets us swap Gemini for another provider (OpenAI, a local
model, …) without touching the Copilot service, routes, or tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

Role = Literal["user", "model"]


@dataclass(frozen=True)
class Turn:
    """A single message in a conversation, in provider-neutral form."""

    role: Role
    text: str


@runtime_checkable
class LLMProvider(Protocol):
    """Anything that can turn a system prompt + conversation into a reply."""

    async def generate(self, *, system: str, history: list[Turn]) -> str: ...
