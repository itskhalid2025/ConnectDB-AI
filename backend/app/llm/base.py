"""
File: base.py (LLM)
Version: 1.1.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: Abstract base classes and data structures for LLM providers. 
             Defines the unified interface that all AI model adapters must implement.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from app.schemas.llm import ModelInfo


@dataclass
class ChatMessage:
    """
    Standardized internal representation of a conversation turn.
    
    Attributes:
        role: The role of the speaker (system, user, or assistant).
        content: The raw text content of the message.
    """
    role: str
    content: str


class LLMProvider(ABC):
    """
    Abstract Strategy interface for AI model adapters.
    
    Ensures that the core application logic remains decoupled from 
    specific LLM provider SDKs (e.g., Google Generative AI, OpenAI, Anthropic).
    """

    name: str

    def __init__(self, api_key: str):
        """
        Args:
            api_key: The provider-specific API key for authentication.
        """
        self.api_key = api_key

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """
        Returns a list of models supported by the provider that are 
        suitable for analytical chat tasks.
        """

    @abstractmethod
    async def chat(
        self,
        *,
        model: str,
        messages: list[ChatMessage],
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str:
        """
        Executes a single, non-streaming chat completion request.
        
        Args:
            model: The ID of the specific model to use.
            messages: The conversation history including the system instruction.
            max_tokens: Limit on the response length.
            temperature: Sampling temperature (0.0 for deterministic results).
            
        Returns:
            The raw text response from the assistant.
        """
