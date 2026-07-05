"""Google Gemini implementation of the LLM provider."""

from __future__ import annotations

from google import genai
from google.genai import types

from app.ai.base import LLMProvider, Turn
from app.core.exceptions import AIError
from app.core.logging import get_logger

logger = get_logger(__name__)


class GeminiProvider(LLMProvider):
    """Async Gemini-backed text generation."""

    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def generate(self, *, system: str, history: list[Turn]) -> str:
        contents = [
            types.Content(role=turn.role, parts=[types.Part(text=turn.text)])
            for turn in history
        ]
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=0.3,
                    max_output_tokens=1024,
                ),
            )
        except Exception as exc:  # noqa: BLE001 - normalise any SDK/network error
            logger.error("gemini_error", error=str(exc))
            raise AIError() from exc

        text = (response.text or "").strip()
        if not text:
            raise AIError("The AI returned an empty response.")
        return text
