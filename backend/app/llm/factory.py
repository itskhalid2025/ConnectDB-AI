from app.core.errors import LLMProviderError
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.base import LLMProvider
from app.llm.gemini_provider import GeminiProvider
from app.llm.openai_provider import OpenAIProvider
from app.schemas.llm import ProviderName


def get_provider(name: ProviderName, api_key: str) -> LLMProvider:
    if name == "openai":
        return OpenAIProvider(api_key)
    if name == "gemini":
        return GeminiProvider(api_key)
    if name == "anthropic":
        return AnthropicProvider(api_key)
    raise LLMProviderError(f"Unknown provider: {name}")
