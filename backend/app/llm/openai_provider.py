from __future__ import annotations

from openai import AsyncOpenAI, OpenAIError

from app.core.errors import LLMProviderError
from app.llm.base import ChatMessage, LLMProvider
from app.schemas.llm import ModelInfo

# Models we surface in the dropdown — everything containing these substrings,
# excluding things that are not chat-capable (embeddings, tts, whisper, etc.).
_CHAT_MODEL_HINTS = ("gpt-4", "gpt-4o", "gpt-3.5", "o1", "o3", "o4")
_EXCLUDE_HINTS = ("embedding", "tts", "whisper", "moderation", "audio", "image", "dall")


import logging
log = logging.getLogger(__name__)

class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self._client = AsyncOpenAI(api_key=api_key)

    async def list_models(self) -> list[ModelInfo]:
        try:
            page = await self._client.models.list()
        except OpenAIError as e:
            raise LLMProviderError(f"OpenAI: {e}", hint="Check your API key.") from e

        models: list[ModelInfo] = []
        for m in page.data:
            mid = m.id
            lower = mid.lower()
            if any(x in lower for x in _EXCLUDE_HINTS):
                continue
            if not any(h in lower for h in _CHAT_MODEL_HINTS):
                continue
            models.append(ModelInfo(id=mid, label=mid))
        models.sort(key=lambda m: m.id)
        return models

    async def chat(
        self,
        *,
        model: str,
        messages: list[ChatMessage],
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str:
        # Log the outgoing prompt
        log.info("OpenAI Request [Model: %s]", model)
        for i, m in enumerate(messages):
            log.info("Message %d [%s]: %s", i, m.role, m.content)

        try:
            resp = await self._client.chat.completions.create(
                model=model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except OpenAIError as e:
            raise LLMProviderError(f"OpenAI: {e}", hint="Check the API key and selected model.") from e

        choice = resp.choices[0]
        output = (choice.message.content or "").strip()
        log.info("OpenAI Response: %s", output)
        return output
