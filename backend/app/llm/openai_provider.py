"""
File: openai_provider.py
Version: 1.1.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: OpenAI API adapter. Implements the LLMProvider interface for 
             GPT models, including automated model discovery and 
             request/response logging.
"""

from __future__ import annotations
import logging
from openai import AsyncOpenAI, OpenAIError

from app.core.errors import LLMProviderError
from app.llm.base import ChatMessage, LLMProvider
from app.schemas.llm import ModelInfo

# Initialize logger
log = logging.getLogger(__name__)

# Filtering heuristics for OpenAI model discovery
_CHAT_MODEL_HINTS = ("gpt-4", "gpt-4o", "gpt-3.5", "o1", "o3", "o4")
_EXCLUDE_HINTS = ("embedding", "tts", "whisper", "moderation", "audio", "image", "dall")


class OpenAIProvider(LLMProvider):
    """
    Adapter for OpenAI's Chat Completion API.
    """
    name = "openai"

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self._client = AsyncOpenAI(api_key=api_key)

    async def list_models(self) -> list[ModelInfo]:
        """
        Fetches and filters the available OpenAI models.
        Only surfaces models suitable for chat-based analytical tasks.
        
        Returns:
            A sorted list of ModelInfo objects.
        """
        try:
            page = await self._client.models.list()
        except OpenAIError as e:
            raise LLMProviderError(f"OpenAI: {e}", hint="Check your API key.") from e

        models: list[ModelInfo] = []
        for m in page.data:
            mid = m.id
            lower = mid.lower()
            # Filter out non-chat models (audio, vision stubs, etc.)
            if any(x in lower for x in _EXCLUDE_HINTS):
                continue
            # Ensure we only include known high-performing chat models
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
        """
        Executes a chat completion request with full logging of the pipeline state.
        
        Args:
            model: Target OpenAI model ID.
            messages: List of standardized ChatMessages.
            max_tokens: Response length limit.
            temperature: Creativity control (0.0 for analytical tasks).
            
        Returns:
            The assistant's text response.
        """
        # Detailed logging for troubleshooting AI reasoning
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
        
        # Log response for auditing and hallucination detection
        log.info("OpenAI Response: %s", output)
        return output
