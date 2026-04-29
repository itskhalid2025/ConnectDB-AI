"""
File: factory.py
Version: 1.1.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: Factory module for LLM providers. Encapsulates the instantiation 
             logic for different AI model adapters, ensuring a consistent 
             interface for the rest of the application.
"""

from app.core.errors import LLMProviderError
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.base import LLMProvider
from app.llm.gemini_provider import GeminiProvider
from app.llm.openai_provider import OpenAIProvider
from app.schemas.llm import ProviderName


def get_provider(name: ProviderName, api_key: str) -> LLMProvider:
    """
    Factory function that returns an initialized LLM Provider instance.
    
    Args:
        name: The name of the provider (openai, gemini, or anthropic).
        api_key: The user's API key for the chosen provider.
        
    Returns:
        An instance of a class implementing the LLMProvider interface.
        
    Raises:
        LLMProviderError: If the requested provider is not supported.
    """
    if name == "openai":
        return OpenAIProvider(api_key)
    if name == "gemini":
        return GeminiProvider(api_key)
    if name == "anthropic":
        return AnthropicProvider(api_key)
    raise LLMProviderError(f"Unknown provider: {name}")
