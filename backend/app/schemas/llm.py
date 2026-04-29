from typing import Literal

from pydantic import BaseModel, Field

ProviderName = Literal["openai", "gemini", "anthropic"]


class ModelInfo(BaseModel):
    id: str
    label: str


class ModelsResponse(BaseModel):
    provider: ProviderName
    models: list[ModelInfo]


class AIConfig(BaseModel):
    provider: ProviderName
    api_key: str = Field(..., min_length=1, max_length=512)
    model: str = Field(..., min_length=1, max_length=128)
