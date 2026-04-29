"""
File: anthropic_provider.py
Version: 1.1.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: Anthropic API adapter. Implements the LLMProvider interface for 
             Claude models. Manages the specialized conversion of system 
             instructions into Anthropic's top-level system parameter.
"""

from __future__ import annotations
import logging
from anthropic import AsyncAnthropic, AnthropicError

from app.core.errors import LLMProviderError
from app.llm.base import ChatMessage, LLMProvider
from app.schemas.llm import ModelInfo

# Initialize logger
log = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """
    Adapter for Anthropic's Messages API.
    """
    name = "anthropic"

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self._client = AsyncAnthropic(api_key=api_key)

    async def list_models(self) -> list[ModelInfo]:
        """
        Fetches available Claude models from the Anthropic API.
        
        Returns:
            A list of ModelInfo objects containing model IDs and display names.
        """
        try:
            page = await self._client.models.list()
        except AnthropicError as e:
            raise LLMProviderError(f"Anthropic: {e}", hint="Check your API key.") from e

        models: list[ModelInfo] = []
        for m in page.data:
            models.append(ModelInfo(id=m.id, label=m.display_name or m.id))
        
        # Sort by ID (descending) to surface newer models (Claude 3.5, 3, etc.) first
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
        """
        Executes a chat completion request using the Anthropic Messages structure.
        
        Special Handling:
        - Extracts 'system' messages into the 'system' top-level parameter.
        - Ensures message history only contains alternating 'user' and 'assistant' roles.
        
        Args:
            model: Target Anthropic model ID.
            messages: List of standardized ChatMessages.
            max_tokens: Response length limit.
            temperature: Creativity control (0.0 for analytical tasks).
            
        Returns:
            The assistant's text response.
        """
        # Anthropic separates system from messages and only allows user/assistant roles.
        system_text = "\n\n".join(m.content for m in messages if m.role == "system")
        chat_msgs = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in ("user", "assistant")
        ]
        
        # Log the outgoing prompt state
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

        # Extract text blocks from response content
        text_parts: list[str] = []
        for block in resp.content:
            if getattr(block, "type", None) == "text":
                text_parts.append(block.text)
        
        output = "".join(text_parts).strip()
        log.info("Anthropic Response: %s", output)
        return output
