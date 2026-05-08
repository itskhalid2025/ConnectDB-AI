"""
File: chat_orchestrator.py
Version: 2.0.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: Enhanced orchestration service implementing a 6-stage AI pipeline.
             Includes classification, self-healing SQL generation, and ambiguity gates.
"""

from __future__ import annotations
import logging
import uuid
import json

from app.core.config import get_settings
from app.core.errors import ConnectDBError, SQLExecutionError
from app.llm.factory import get_provider
from app.llm.prompts import (
    build_sql_messages,
    build_insight_messages,
    build_chart_intelligence_messages,
    build_recovery_messages,
    build_clarify_messages
)
from app.schemas.chat import ChatResponse, ChatTurn, ErrorPayload
from app.schemas.llm import AIConfig
from app.services.analyzer import build_chart
from app.services.query_classifier import classify_query
from app.services.schema_builder import build_schema_context
from app.services.session_store import Session
from app.services.sql_executor import execute as execute_sql
from app.services.sql_guard import validate as validate_sql

log = logging.getLogger(__name__)

async def handle_message(
    session: Session,
    *,
    question: str,
    ai_config: AIConfig,
) -> ChatResponse:
    """
    Enhanced Orchestration Pipeline (v2.0.0):
    1. Classify Intent & Check Clarity
    2. Ambiguity Gate (Stage 6)
    3. Generate SQL (Stage 2)
    4. Execute & Self-Heal (Stage 5)
    5. Chart Intelligence (Stage 3)
    6. Insight Synthesis (Stage 4)
    """
    settings = get_settings()
    message_id = uuid.uuid4().hex
    provider = get_provider(ai_config.provider, ai_config.api_key)
    schema_text = build_schema_context(session.schema)
    
    # --- Stage 1: Classification & Stage 6: Ambiguity Gate ---
    classification = await classify_query(
        provider, ai_config.model, question, schema_text
    )
    
    if classification["clarity_score"] < 0.7:
        clarification = await provider.chat(
            model=ai_config.model,
            messages=build_clarify_messages(question, schema_text, classification["reason"]),
            max_tokens=300
        )
        return ChatResponse(
            message_id=message_id,
            insights=clarification,
            needs_clarification=True,
            classification=classification["strategy"]
        )

    # --- Stage 2: SQL Generation ---
    history_window = session.history[-settings.chat_history_turns * 2 :]
    sql_messages = build_sql_messages(
        question=question,
        schema_text=schema_text,
        strategy=classification["strategy"],
        business_notes=session.notes,
        history=history_window
    )
    
    try:
        raw_sql = await provider.chat(
            model=ai_config.model,
            messages=sql_messages,
            max_tokens=800,
            temperature=0.0
        )
    except ConnectDBError as e:
        return _error_response(message_id, e)

    if "-- cannot answer" in raw_sql.lower():
        return ChatResponse(message_id=message_id, insights="I couldn't find a way to answer that with the current schema.")

    # --- Stage 4 & 5: Execution & Self-Healing ---
    safe_sql = ""
    table = None
    retry_count = 0
    max_retries = 1
    current_sql = raw_sql

    while retry_count <= max_retries:
        try:
            safe_sql = validate_sql(current_sql, max_rows=settings.max_result_rows)
            table = await execute_sql(
                session.pool,
                safe_sql,
                timeout_seconds=settings.query_timeout_seconds,
                max_rows=settings.max_result_rows
            )
            break # Success
        except (SQLExecutionError, UnsafeSQLError) as e:
            if retry_count < max_retries:
                log.warning("SQL failed or was invalid, attempting self-healing retry. Error: %s", e)
                recovery_msgs = build_recovery_messages(question, schema_text, current_sql, str(e))
                current_sql = await provider.chat(model=ai_config.model, messages=recovery_msgs)
                retry_count += 1
            else:
                return _error_response(message_id, e, sql=current_sql)
        except Exception as e:
             return _error_response(message_id, ConnectDBError(str(e), stage="orchestrator"), sql=current_sql)

    # --- Stage 3: Chart Intelligence ---
    chart = None
    try:
        intel_raw = await provider.chat(
            model=ai_config.model,
            messages=build_chart_intelligence_messages(question, table),
            max_tokens=200,
            temperature=0.0
        )
        # Parse JSON
        clean_intel = intel_raw.strip()
        if clean_intel.startswith("```"):
            clean_intel = clean_intel.split("```")[1]
            if clean_intel.startswith("json"):
                clean_intel = clean_intel[4:].strip()
        intel = json.loads(clean_intel)
        
        if intel.get("score", 0) >= 7:
            chart = build_chart(table, question=question, preferred_type=intel.get("chart_type"))
    except Exception as e:
        log.warning("Chart intel failed: %s", e)
        chart = build_chart(table, question=question)

    # --- Stage 4: Insight Synthesis ---
    try:
        insight = await provider.chat(
            model=ai_config.model,
            messages=build_insight_messages(question, table),
            max_tokens=400,
            temperature=0.2
        )
    except Exception:
        insight = "Analysis complete. See data below."

    # Update history
    session.history.append(ChatTurn(role="user", content=question))
    session.history.append(ChatTurn(role="assistant", content=insight))

    return ChatResponse(
        message_id=message_id,
        sql=safe_sql,
        table=table,
        chart=chart,
        insights=insight,
        classification=classification["strategy"]
    )

def _error_response(message_id: str, exc: ConnectDBError, sql: str | None = None) -> ChatResponse:
    return ChatResponse(
        message_id=message_id,
        sql=sql,
        error=ErrorPayload(stage=exc.stage, message=str(exc), hint=getattr(exc, "hint", ""))
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
