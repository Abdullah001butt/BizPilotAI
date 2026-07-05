"""AI Copilot endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CopilotServiceDep, CurrentUser, RequirePro
from app.core.config import settings
from app.schemas.copilot import ChatRequest, ChatResponse, CopilotStatus

router = APIRouter(prefix="/copilot", tags=["copilot"])


@router.get("/status", response_model=CopilotStatus, summary="Copilot availability")
async def status(_: CurrentUser) -> CopilotStatus:
    """Report whether the Copilot is configured (has an API key)."""
    return CopilotStatus(
        configured=settings.is_ai_configured,
        model=settings.GEMINI_MODEL if settings.is_ai_configured else None,
    )


@router.post("/chat", response_model=ChatResponse, summary="Ask the Copilot")
async def chat(data: ChatRequest, service: CopilotServiceDep, _: RequirePro) -> ChatResponse:
    """Answer a question grounded in the company's live business data (Pro plan)."""
    answer = await service.ask(data.messages)
    return ChatResponse(message=answer)
