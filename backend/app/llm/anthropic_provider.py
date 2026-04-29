from __future__ import annotations

from anthropic import AsyncAnthropic, AnthropicError

from app.core.errors import LLMProviderError
from app.llm.base import ChatMessage, LLMProvider
from app.schemas.llm import ModelInfo


import logging
log = logging.getLogger(__name__)

class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self._client = AsyncAnthropic(api_key=api_key)

    async def list_models(self) -> list[ModelInfo]:
        try:
            page = await self._client.models.list()
        except AnthropicError as e:
            raise LLMProviderError(f"Anthropic: {e}", hint="Check your API key.") from e

        models: list[ModelInfo] = []
        for m in page.data:
            models.append(ModelInfo(id=m.id, label=m.display_name or m.id))
        models.sort(key=lambda m: m.id, reverse=True)
        return models

    async def chat(
        self,
        *,
        model: str,
        messages: list[ChatMessage],
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str:
        # Anthropic separates system from messages and only allows user/assistant roles.
        system_text = "\n\n".join(m.content for m in messages if m.role == "system")
        chat_msgs = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in ("user", "assistant")
        ]
        
        # Log the outgoing prompt
        log.info("Anthropic Request [Model: %s]", model)
        if system_text:
            log.info("System Prompt: %s", system_text)
        for i, m in enumerate(chat_msgs):
            log.info("Message %d [%s]: %s", i, m["role"], m["content"])

        if not chat_msgs:
            raise LLMProviderError("No user message to send.", hint="Internal error.")

        try:
            resp = await self._client.messages.create(
                model=model,
                system=system_text or None,
                messages=chat_msgs,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except AnthropicError as e:
            raise LLMProviderError(f"Anthropic: {e}", hint="Check the API key and selected model.") from e

        text_parts: list[str] = []
        for block in resp.content:
            if getattr(block, "type", None) == "text":
                text_parts.append(block.text)
        output = "".join(text_parts).strip()
        log.info("Anthropic Response: %s", output)
        return output
