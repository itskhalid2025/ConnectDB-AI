"""
File: llm.py
Version: 1.1.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: API Routes for LLM provider interaction. Handles model discovery 
             and metadata retrieval for supported AI providers (e.g., Gemini).
"""

from fastapi import APIRouter, Query

from app.llm.factory import get_provider
from app.schemas.llm import ModelsResponse, ProviderName

# Initialize router
router = APIRouter()


@router.get("/models", response_model=ModelsResponse)
async def list_models(
    provider: ProviderName = Query(...),
    api_key: str = Query(..., min_length=1, max_length=512),
) -> ModelsResponse:
    """
    Fetches the list of available models from the specified AI provider.
    
    Args:
        provider: The provider name (e.g., 'gemini').
        api_key: The user's API key for authentication with the provider.
        
    Returns:
        A list of model identifiers supported by the provider.
    """
    adapter = get_provider(provider, api_key)
    models = await adapter.list_models()
    return ModelsResponse(provider=provider, models=models)
