"""End-to-end NL → SQL → execute → analyse pipeline."""

from __future__ import annotations

import logging
import uuid

from app.core.config import get_settings
from app.core.errors import ConnectDBError, UnsafeSQLError
from app.llm.factory import get_provider
from app.llm.prompts import build_insight_messages, build_sql_messages
from app.schemas.chat import ChatResponse, ChatTurn, ErrorPayload
from app.schemas.llm import AIConfig
from app.services.analyzer import build_chart
from app.services.schema_inspector import render_schema_for_prompt
from app.services.session_store import Session
from app.services.sql_executor import execute as execute_sql
from app.services.sql_guard import validate as validate_sql

log = logging.getLogger(__name__)

CANNOT_ANSWER_MARKER = "-- cannot answer"


async def handle_message(
    session: Session,
    *,
    question: str,
    ai_config: AIConfig,
) -> ChatResponse:
    settings = get_settings()
    message_id = uuid.uuid4().hex
    provider = get_provider(ai_config.provider, ai_config.api_key)
    history_window = session.history[-settings.chat_history_turns * 2 :]

    # Step 1: generate SQL
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
            temperature=0.0,
        )
    except ConnectDBError as e:
        return _error_response(message_id, e)

    if CANNOT_ANSWER_MARKER in raw_sql.lower():
        msg = "I don't have enough schema information to answer that."
        session.history.append(ChatTurn(role="user", content=question))
        session.history.append(ChatTurn(role="assistant", content=msg))
        return ChatResponse(message_id=message_id, insights=msg)

    # Step 2: validate
    is_sql = "select" in raw_sql.lower() or "with" in raw_sql.lower()
    
    if not is_sql:
        # If it doesn't look like SQL, treat it as a direct text response/greeting
        # Strip any leading "-- " markers if the AI used them for the greeting
        clean_msg = raw_sql.strip()
        if clean_msg.startswith("--"):
            clean_msg = clean_msg.lstrip("-").strip()
            
        session.history.append(ChatTurn(role="user", content=question))
        session.history.append(ChatTurn(role="assistant", content=clean_msg))
        return ChatResponse(message_id=message_id, insights=clean_msg)

    try:
        safe_sql = validate_sql(raw_sql, max_rows=settings.max_result_rows)
    except UnsafeSQLError as e:
        # If it was actually meant to be SQL but failed validation
        return _error_response(message_id, e, sql=raw_sql)

    # Step 3: execute
    try:
        table = await execute_sql(
            session.pool,
            safe_sql,
            timeout_seconds=settings.query_timeout_seconds,
            max_rows=settings.max_result_rows,
        )
    except ConnectDBError as e:
        return _error_response(message_id, e, sql=safe_sql)

    # Step 4: chart heuristic + insight
    chart = build_chart(table, question=question)
    insight = ""
    try:
        insight_messages = build_insight_messages(question=question, table=table)
        insight = await provider.chat(
            model=ai_config.model,
            messages=insight_messages,
            max_tokens=300,
            temperature=0.2,
        )
    except ConnectDBError as e:
        # Insight generation is best-effort — don't fail the whole turn.
        log.warning("Insight generation failed: %s", e)
        insight = "Results are shown below."

    # Step 5: append to history (we intentionally only keep the question + insight,
    # not the SQL, to keep history compact for future turns)
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
    return ChatResponse(
        message_id=message_id,
        sql=sql,
        error=ErrorPayload(stage=exc.stage, message=exc.message, hint=exc.hint),
    )
