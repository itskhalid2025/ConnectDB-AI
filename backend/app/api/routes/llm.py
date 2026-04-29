from fastapi import APIRouter, Query

from app.llm.factory import get_provider
from app.schemas.llm import ModelsResponse, ProviderName

router = APIRouter()


@router.get("/models", response_model=ModelsResponse)
async def list_models(
    provider: ProviderName = Query(...),
    api_key: str = Query(..., min_length=1, max_length=512),
) -> ModelsResponse:
    adapter = get_provider(provider, api_key)
    models = await adapter.list_models()
    return ModelsResponse(provider=provider, models=models)
