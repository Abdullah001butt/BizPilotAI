"""AI Copilot business logic — grounds the LLM in live company data."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import LLMProvider, Turn
from app.ai.context import build_business_context
from app.core.exceptions import AIUnavailableError
from app.core.logging import get_logger
from app.models.company import Company
from app.schemas.copilot import ChatMessage

logger = get_logger(__name__)

_SYSTEM_TEMPLATE = """You are BizPilot AI, an expert business copilot embedded in \
the {company} dashboard. You help the owner run their business by answering \
questions and giving concrete, actionable advice.

Use ONLY the live business data below to answer. If the data does not contain \
the answer, say so plainly rather than inventing numbers. Be concise, specific, \
and practical. Format money in the company's currency. When useful, suggest a \
clear next action.

=== LIVE BUSINESS DATA ===
{context}
=== END DATA ==="""


class CopilotService:
    def __init__(
        self, session: AsyncSession, company: Company, provider: LLMProvider | None
    ) -> None:
        self.session = session
        self.company = company
        self.provider = provider

    async def ask(self, messages: list[ChatMessage]) -> str:
        """Answer the latest question grounded in the company's live data."""
        if self.provider is None:
            raise AIUnavailableError()

        context = await build_business_context(self.session, self.company)
        system = _SYSTEM_TEMPLATE.format(company=self.company.name, context=context)

        history = [
            Turn(role="model" if m.role == "assistant" else "user", text=m.content)
            for m in messages
        ]
        answer = await self.provider.generate(system=system, history=history)
        logger.info("copilot_answered", company_id=self.company.id, turns=len(history))
        return answer
