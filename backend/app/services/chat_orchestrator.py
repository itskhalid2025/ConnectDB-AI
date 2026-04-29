"""
File: chat_orchestrator.py
Version: 1.1.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: Core orchestration service that manages the end-to-end flow of natural language 
             to SQL generation, safety validation, database execution, and analytical insight synthesis.
"""

from __future__ import annotations

import logging
import uuid
import json

from app.core.config import get_settings
from app.core.errors import ConnectDBError, UnsafeSQLError
from app.llm.factory import get_provider
from app.llm.prompts import (
    build_insight_messages, 
    build_sql_messages,
    build_chart_intelligence_messages
)
from app.schemas.chat import ChatResponse, ChatTurn, ErrorPayload
from app.llm.base import ChatMessage
from app.schemas.llm import AIConfig
from app.services.analyzer import build_chart
from app.services.schema_inspector import render_schema_for_prompt
from app.services.session_store import Session
from app.services.sql_executor import execute as execute_sql
from app.services.sql_guard import validate as validate_sql

# Initialize logger for orchestration events
log = logging.getLogger(__name__)

# Token used by the LLM to signal it cannot satisfy a query with the current schema
CANNOT_ANSWER_MARKER = "-- cannot answer"


async def handle_message(
    session: Session,
    *,
    question: str,
    ai_config: AIConfig,
) -> ChatResponse:
    """
    Main orchestration entry point for a single chat turn.
    
    Workflow:
    1. Generate raw SQL using the configured LLM provider.
    2. Validate SQL for safety and read-only constraints.
    3. Execute SQL against the target database.
    4. Heuristically select a chart and generate analytical insights.
    5. Maintain session history for multi-turn conversations.
    
    Args:
        session: Current user session object containing DB pool and schema.
        question: The natural language question from the user.
        ai_config: Configuration for the LLM (provider, model, API key).
        
    Returns:
        ChatResponse object containing SQL, data, chart, and insights.
    """
    settings = get_settings()
    message_id = uuid.uuid4().hex
    provider = get_provider(ai_config.provider, ai_config.api_key)
    
    # Calculate history window for context
    history_window = session.history[-settings.chat_history_turns * 2 :]

    # --- Step 1: SQL Generation ---
    try:
        sql_messages = build_sql_messages(
            question=question,
            schema_text=render_schema_for_prompt(session.schema),
            business_notes=session.notes,
            history=history_window,
        )
        raw_sql = await provider.chat(
            model=ai_config.model,
            messages=sql_messages,
            max_tokens=800,
            temperature=0.0, # Zero temperature for deterministic SQL
        )
    except ConnectDBError as e:
        return _error_response(message_id, e)

    # Handle explicit "cannot answer" case
    if CANNOT_ANSWER_MARKER in raw_sql.lower():
        msg = "I don't have enough schema information to answer that."
        session.history.append(ChatTurn(role="user", content=question))
        session.history.append(ChatTurn(role="assistant", content=msg))
        return ChatResponse(message_id=message_id, insights=msg)

    # --- Step 2: Safety & Intent Validation ---
    # Determine if the response is SQL or a conversational greeting
    is_sql = "select" in raw_sql.lower() or "with" in raw_sql.lower()
    
    if not is_sql:
        # Treatment for direct text responses (Greetings, capability questions)
        clean_msg = raw_sql.strip()
        if clean_msg.startswith("--"):
            clean_msg = clean_msg.lstrip("-").strip()
            
        session.history.append(ChatTurn(role="user", content=question))
        session.history.append(ChatTurn(role="assistant", content=clean_msg))
        return ChatResponse(message_id=message_id, insights=clean_msg)

    try:
        # Guard against destructive or non-performant queries
        safe_sql = validate_sql(raw_sql, max_rows=settings.max_result_rows)
    except UnsafeSQLError as e:
        return _error_response(message_id, e, sql=raw_sql)

    # --- Step 3: Database Execution ---
    try:
        table = await execute_sql(
            session.pool,
            safe_sql,
            timeout_seconds=settings.query_timeout_seconds,
            max_rows=settings.max_result_rows,
        )
    except ConnectDBError as e:
        return _error_response(message_id, e, sql=safe_sql)

    # --- Step 4: Analytical Synthesis ---
    # Intelligent Chart Selection: Rate the need for a chart (0-10)
    chart = None
    try:
        chart_intel_messages = build_chart_intelligence_messages(question=question, table=table)
        intel_raw = await provider.chat(
            model=ai_config.model,
            messages=chart_intel_messages,
            max_tokens=200,
            temperature=0.0,
        )
        # Handle potential markdown backticks in LLM response
        clean_intel = intel_raw.strip()
        if clean_intel.startswith("```"):
            clean_intel = clean_intel.split("```")[1]
            if clean_intel.startswith("json"):
                clean_intel = clean_intel[4:].strip()
        
        intel = json.loads(clean_intel)
        log.info("Chart Intelligence: Score=%s, Type=%s, Reason=%s", 
                 intel.get("score"), intel.get("chart_type"), intel.get("reason"))
        
        if intel.get("score", 0) >= 7:
            chart = build_chart(
                table, 
                question=question, 
                preferred_type=intel.get("chart_type")
            )
    except Exception as e:
        log.warning("Chart Intelligence failed, falling back to heuristics: %s", e)
        chart = build_chart(table, question=question)

    insight = ""
    try:
        # Summarize the data in plain English (Senior Data Engineer tone)
        insight_messages = build_insight_messages(question=question, table=table)
        insight = await provider.chat(
            model=ai_config.model,
            messages=insight_messages,
            max_tokens=300,
            temperature=0.2, # Slight temperature for natural phrasing
        )
    except ConnectDBError as e:
        log.warning("Insight generation failed: %s", e)
        insight = "Results are shown below."

    # --- Step 5: Session State Management ---
    # Persist the turn to history for future context
    session.history.append(ChatTurn(role="user", content=question))
    session.history.append(ChatTurn(role="assistant", content=insight))

    return ChatResponse(
        message_id=message_id,
        sql=safe_sql,
        table=table,
        chart=chart,
        insights=insight,
    )


def _error_response(
    message_id: str, exc: ConnectDBError, *, sql: str | None = None
) -> ChatResponse:
    """Standardized error wrapper for chat responses."""
    return ChatResponse(
        message_id=message_id,
        sql=sql,
        error=ErrorPayload(stage=exc.stage, message=exc.message, hint=exc.hint),
    )
