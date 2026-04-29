"""
File: llm.py (Schemas)
Version: 1.1.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: Pydantic models for LLM provider configuration and metadata. 
             Defines the structures for model discovery and session-level AI settings.
"""

from typing import Literal
from pydantic import BaseModel, Field

# Supported AI Providers
ProviderName = Literal["openai", "gemini", "anthropic"]


class ModelInfo(BaseModel):
    """Metadata for a specific AI model."""
    id: str
    label: str


class ModelsResponse(BaseModel):
    """Response containing available models for a specific provider."""
    provider: ProviderName
    models: list[ModelInfo]


class AIConfig(BaseModel):
    """
    Configuration for an AI-powered request.
    Passed along with the user's question to specify the target model and credentials.
    """
    provider: ProviderName
    api_key: str = Field(..., min_length=1, max_length=512)
    model: str = Field(..., min_length=1, max_length=128)
