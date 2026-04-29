"""
File: chat.py (Schemas)
Version: 1.1.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: Pydantic models for chat-related data structures. Defines the 
             contracts for requests, responses, and internal chat history.
"""

from typing import Any, Literal
from pydantic import BaseModel, Field
from app.schemas.llm import AIConfig


class ChatRequest(BaseModel):
    """Payload for submitting a new message to the chat pipeline."""
    question: str = Field(..., min_length=1, max_length=4000)
    ai_config: AIConfig


class TableResult(BaseModel):
    """Structured representation of a SQL query result set."""
    columns: list[str]
    rows: list[list[Any]]
    truncated: bool = False


class ChartSpec(BaseModel):
    """
    Standardized visualization specification. 
    Compatible with Plotly on the frontend.
    """
    data: list[dict[str, Any]]
    layout: dict[str, Any] = Field(default_factory=dict)


class ErrorPayload(BaseModel):
    """Detailed error information for the frontend UI."""
    stage: str
    message: str
    hint: str


class ChatResponse(BaseModel):
    """
    The unified response object for a chat interaction. 
    May contain partial results if the pipeline fails at a specific stage.
    """
    message_id: str
    sql: str | None = None
    table: TableResult | None = None
    chart: ChartSpec | None = None
    insights: str | None = None
    error: ErrorPayload | None = None
    
    # --- New Fields for v2.0.0 Pipeline ---
    classification: str | None = None
    explanation: str | None = None
    needs_clarification: bool = False


class ChatTurn(BaseModel):
    """Represents a single exchange in the conversation history."""
    role: Literal["user", "assistant"]
    content: str
