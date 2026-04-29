from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.schemas.llm import ModelInfo


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


class LLMProvider(ABC):
    """Strategy interface implemented by each provider adapter.

    The orchestrator only ever talks to this surface; provider-specific SDK
    types stay confined to the adapter implementations.
    """

    name: str

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """Return models that look usable for chat/completion."""

    @abstractmethod
    async def chat(
        self,
        *,
        model: str,
        messages: list[ChatMessage],
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str:
        """Run a single non-streaming chat completion. Returns the assistant text."""
