from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.llm import AIConfig


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    ai_config: AIConfig


class TableResult(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
    truncated: bool = False


class ChartSpec(BaseModel):
    """Subset of a Plotly figure: data + layout."""

    data: list[dict[str, Any]]
    layout: dict[str, Any] = Field(default_factory=dict)


class ErrorPayload(BaseModel):
    stage: str
    message: str
    hint: str


class ChatResponse(BaseModel):
    message_id: str
    sql: str | None = None
    table: TableResult | None = None
    chart: ChartSpec | None = None
    insights: str | None = None
    error: ErrorPayload | None = None


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str
