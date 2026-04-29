"""
File: prompts.py
Version: 1.2.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: Standardized prompt templates for the SQL-generation and result-analysis steps.
             Ensures strict output formats for deterministic processing and high-quality 
             analytical insights.
"""

from __future__ import annotations

import json

from app.llm.base import ChatMessage
from app.schemas.chat import ChatTurn, TableResult

# -----------------------------------------------------------------------------
# SQL Generation Prompt
# -----------------------------------------------------------------------------
SQL_SYSTEM_PROMPT = """\
You are a senior PostgreSQL analyst who writes precise read-only SQL.

Rules — follow ALL of them:
1. Output ONLY a single PostgreSQL SELECT statement. No prose, no comments, no markdown fences.
2. The query MUST be read-only. Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, GRANT, MERGE, COPY, or anything that mutates state.
3. Use only the tables and columns in the provided schema. If the user's question can't be answered with the available schema, output exactly: -- cannot answer
4. If the user greets you or asks general questions about the application's capabilities (e.g., chart types, how to use it), provide a helpful response in plain English, but DO NOT write any SQL.
5. Honour the business definitions verbatim — they are authoritative.
6. Prefer explicit column lists over SELECT *.
7. When grouping or ordering by a derived column, give it a clear alias.
8. When a question implies a time series, ORDER BY the time dimension ascending.
9. Default to LIMIT 1000 when the result set could be large.
10. BE EXTREMELY CAREFUL with column names. Do not assume. For example, many tables use 'id' as their primary key, even if other tables refer to it as 'user_id' or 'invoice_id'. Use the EXACT name shown in the schema.
"""


def build_sql_messages(
    *,
    question: str,
    schema_text: str,
    business_notes: str,
    history: list[ChatTurn],
) -> list[ChatMessage]:
    """
    Constructs a chat payload for the SQL generation LLM call.
    
    Args:
        question: The user's natural language question.
        schema_text: A text representation of the target database schema.
        business_notes: authoritatively provided user definitions.
        history: List of previous chat turns for contextual continuity.
        
    Returns:
        A list of ChatMessage objects (System + User).
    """
    history_block = ""
    if history:
        rendered = "\n".join(f"{t.role.upper()}: {t.content}" for t in history)
        history_block = f"\n\nRecent conversation (most recent last):\n{rendered}"

    notes_block = (
        f"\n\nBusiness definitions provided by the user (treat as authoritative):\n{business_notes}"
        if business_notes.strip()
        else ""
    )

    user_prompt = (
        f"Database schema:\n{schema_text}"
        f"{notes_block}"
        f"{history_block}"
        f"\n\nUser question: {question}\n\n"
        "Return only the SQL statement."
    )
    return [
        ChatMessage(role="system", content=SQL_SYSTEM_PROMPT),
        ChatMessage(role="user", content=user_prompt),
    ]


# -----------------------------------------------------------------------------
# Insight Generation Prompt
# -----------------------------------------------------------------------------
INSIGHT_SYSTEM_PROMPT = """\
You are a Senior Analytical Data Engineer. Your goal is to provide high-level executive summaries of data results.

Rules:
1. Tone: Professional, technical, and objective. Avoid fluff.
2. Depth: Don't just restate numbers; analyze proportions, trends, and significance.
3. Context: If the data allows, calculate percentages or identify the most significant contributor (e.g., "The 'Paid' segment accounts for 61% of total revenue").
4. Formatting: Keep it to 2-4 sentences. Use clear terminology (e.g., 'distribution', 'volume', 'concentration').
5. If the data is empty, provide a professional note on the lack of matching records for the criteria.
"""


def build_insight_messages(
    *,
    question: str,
    table: TableResult,
    max_rows_in_prompt: int = 50,
) -> list[ChatMessage]:
    """
    Constructs a chat payload for the data-analysis (insight) LLM call.
    
    Args:
        question: Original user question for context.
        table: The result table returned from SQL execution.
        max_rows_in_prompt: Safety cap for the number of rows sent to the LLM.
        
    Returns:
        A list of ChatMessage objects (System + User).
    """
    sample_rows = table.rows[:max_rows_in_prompt]
    payload = {
        "columns": table.columns,
        "row_count": len(table.rows),
        "sample_rows": sample_rows,
        "truncated": table.truncated or len(table.rows) > max_rows_in_prompt,
    }
    user_prompt = (
        f"User question: {question}\n\n"
        f"Query result (JSON, possibly sampled):\n{json.dumps(payload, default=str)}\n\n"
        "Write the summary now."
    )
    return [
        ChatMessage(role="system", content=INSIGHT_SYSTEM_PROMPT),
        ChatMessage(role="user", content=user_prompt),
    ]
