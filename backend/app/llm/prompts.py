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
4. If the user asks for data along with a request for a chart, graph, or visualization, you MUST still generate the appropriate SQL query to fetch the data. Only provide a plain English response if the user is ONLY asking about capabilities (e.g., "What charts do you support?") without requesting a specific data search.
5. Honour the business definitions verbatim — they are authoritative. Users may provide descriptions of the database, tables, schema, or specific column logic here.
6. Prefer explicit column lists over SELECT *.
7. When grouping or ordering by a derived column, give it a clear alias.
8. When a question implies a time series, ORDER BY the time dimension ascending.
9. Default to LIMIT 1000 when the result set could be large.
10. BE EXTREMELY CAREFUL with column names. Do not assume. Use the EXACT name shown in the schema.
11. SCALAR SUBQUERIES: If a query needs to return a list of items (e.g., "Top 3 Users" or "All Names") alongside a summary (e.g., "Total Count"), you MUST ensure the subquery returns exactly one row. The SAFEST way to do this is to wrap the list logic in a subquery and aggregate it at the top level. If the list involves "Top N" items based on an aggregate (like spend), ensure you GROUP BY the entity (e.g., user name) first so each entity appears only once.
12. DATA SHAPING FOR CHARTS: If the user asks for a specific chart type (e.g., "Pie Chart" or "Bar Chart"), ensure the SQL returns columns that support that visualization (e.g., Category and Value for Pie/Bar).
13. TABLE INFERENCE: Map natural language terms to the most likely schema tables (e.g., "bills" or "claims" -> 'invoices'; "clients" -> 'users').
14. ROBUST FILTERING: When filtering by user-provided names, use ILIKE and handle potential trailing spaces if necessary (e.g., TRIM(name) ILIKE 'value' or name ILIKE '%value%').
15. ENTITY JOINS: If the user refers to a person by name, JOIN the primary table (e.g., invoices) with the identity table (e.g., users) to filter by the name column, rather than assuming the name exists in the primary table's metadata columns.

Example for "Total users and top 3 spenders":
SELECT 
  (SELECT COUNT(*) FROM users) as total_users,
  (SELECT ARRAY_AGG(name) FROM (SELECT name FROM users ORDER BY total_spend DESC LIMIT 3) AS sub) as top_3_spenders;

Example for "Total users and all names alphabetically":
SELECT 
  (SELECT COUNT(*) FROM users) as total_users,
  (SELECT ARRAY_AGG(name) FROM (SELECT name FROM users ORDER BY name ASC) AS sub) as all_names;
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
# Chart Intelligence Prompt
# -----------------------------------------------------------------------------
CHART_SYSTEM_PROMPT = """\
You are a Data Visualization Expert. 
Analyze the user's question and the structure of the data result.

Task:
1. Rate if a chart is needed to answer this question on a scale of 0-10.
   - Score 10: User explicitly asked for a graph/chart AND data supports it.
   - Score 8-9: Data has clear trends, distributions, or comparisons that are hard to read in text.
   - Score 0-3: Data is a simple list of names or empty.
2. Recommend the best chart type (bar, line, pie, scatter, heatmap, area, indicator).
   - Use 'indicator' for single numeric values (counts, totals).

Rules:
- Return ONLY a JSON object with keys: "score" (int), "chart_type" (string), "reason" (string).
"""


def build_chart_intelligence_messages(
    *,
    question: str,
    table: TableResult,
) -> list[ChatMessage]:
    """Constructs the payload to ask the LLM for a chart recommendation."""
    columns_text = ", ".join(table.columns)
    row_count = len(table.rows)
    
    user_prompt = (
        f"User question: {question}\n\n"
        f"Data Columns: [{columns_text}]\n"
        f"Number of rows: {row_count}\n"
        "Should we show a chart? Return JSON."
    )
    return [
        ChatMessage(role="system", content=CHART_SYSTEM_PROMPT),
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
