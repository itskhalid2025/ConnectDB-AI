"""
File: prompts.py
Version: 2.0.0
Created At: 2026-04-25
Updated At: 2026-04-29

Description:
    Standardized prompt templates for the full AI analytics pipeline:
    
    Pipeline stages:
        1. Query Classification  — understand intent before touching SQL
        2. SQL Generation        — precise, schema-aware PostgreSQL
        3. Chart Intelligence    — type-aware visualization recommendation
        4. Insight Generation    — executive-grade analytical narrative
        5. Error Recovery        — self-healing SQL correction
        6. Clarification         — ask user when question is ambiguous

    Design principles:
        - Every prompt is deterministic: output format is strictly defined
        - Every prompt is self-contained: no implicit context assumptions
        - Every prompt degrades gracefully: defined fallback outputs
        - Prompts compose, not compete: each stage feeds the next cleanly
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Optional

from app.llm.base import ChatMessage
from app.schemas.chat import ChatTurn, TableResult


# =============================================================================
# ENUMS — Shared intent taxonomy used across all prompts
# =============================================================================

class QueryIntent(str, Enum):
    """
    Canonical intent types detected in stage 1.
    Each maps to a different SQL generation strategy.
    """
    AGGREGATION   = "aggregation"    # COUNT, SUM, AVG — single summary row
    TREND         = "trend"          # Time series — needs ORDER BY time ASC
    COMPARISON    = "comparison"     # A vs B — needs CASE or multiple CTEs
    RANKING       = "ranking"        # TOP N — needs ORDER BY + LIMIT
    DISTRIBUTION  = "distribution"   # Breakdown by category — GROUP BY
    LOOKUP        = "lookup"         # Find specific record(s) — WHERE filter
    DRILL_DOWN    = "drill_down"     # Detail of a previously mentioned result
    CAPABILITY    = "capability"     # "What can you do?" — no SQL needed
    UNKNOWN       = "unknown"        # Fallback — proceed with best effort


class ChartType(str, Enum):
    """Supported visualization types."""
    BAR        = "bar"
    LINE       = "line"
    PIE        = "pie"
    SCATTER    = "scatter"
    HEATMAP    = "heatmap"
    AREA       = "area"
    INDICATOR  = "indicator"   # Single KPI value
    TABLE      = "table"       # Fallback: just show data as table
    NONE       = "none"        # No chart needed


# =============================================================================
# STAGE 1 — Query Classification Prompt
# =============================================================================

CLASSIFY_SYSTEM_PROMPT = """\
You are a query intent classifier for a SQL analytics assistant.

Your ONLY job is to classify the user's question into one of these intent types:

  aggregation  — User wants a summary metric: count, sum, average, total.
                 Example: "How many users do we have?" / "Total revenue?"

  trend        — User wants data over time.
                 Example: "Monthly sales trend" / "Daily signups this year"

  comparison   — User wants A vs B.
                 Example: "Compare this month vs last month" / "Revenue by region"

  ranking      — User wants ordered top/bottom N items.
                 Example: "Top 5 customers" / "Worst performing products"

  distribution — User wants a categorical breakdown.
                 Example: "Sales by department" / "Orders by status"

  lookup       — User wants a specific record or filtered list.
                 Example: "Show orders for customer John" / "Find invoice #1234"

  drill_down   — User is following up on a previous result to go deeper.
                 Example: "Show me the details for that top customer"

  capability   — User is asking about the system, not the data.
                 Example: "What charts do you support?" / "What can you do?"

  unknown      — Cannot be classified with confidence.

Output Rules:
- Return ONLY a valid JSON object. No prose. No markdown.
- Schema:
  {
    "strategy": "<one of the intent types above>",
    "clarity_score": <0.0 to 1.0>,
    "reason": "<one sentence explaining the classification>"
  }
"""


def build_classifier_messages(
    question: str,
    schema_text: str,
) -> list[ChatMessage]:
    """
    Stage 1: Classify the user's question before attempting SQL generation.
    """
    user_prompt = (
        f"Database Schema:\n{schema_text}\n\n"
        f"Question: {question}\n\n"
        "Return JSON only."
    )

    return [
        ChatMessage(role="system", content=CLASSIFY_SYSTEM_PROMPT),
        ChatMessage(role="user", content=user_prompt),
    ]


# =============================================================================
# STAGE 2 — SQL Generation Prompt
# =============================================================================

# -----------------------------------------------------------------------------
# Core SQL rules — always applied
# -----------------------------------------------------------------------------
_SQL_RULES_CORE = """\
ABSOLUTE RULES (never violate):
R1.  Output ONLY a single PostgreSQL SELECT statement. Zero prose, zero markdown fences.
R2.  Read-only. Never use: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE,
     GRANT, REVOKE, MERGE, COPY, EXECUTE, PERFORM, or any DDL/DML.
R3.  Use ONLY tables and columns that exist in the provided schema.
     If the question cannot be answered: output exactly the string -- cannot answer
R4.  Honour business definitions verbatim — they override your assumptions.
R5.  Prefer explicit column lists. Never use SELECT *.
R6.  Always alias derived or computed columns clearly.
R7.  Apply LIMIT 1000 when result set could be large, unless user specifies a count.
R8.  Use EXACT column names from schema. Do not invent or guess column names.
R9.  Use $1, $2 style params only if values were given — otherwise embed literals.
R10. Use CTEs (WITH clauses) for complex multi-step logic. Prefer readability.
"""

# -----------------------------------------------------------------------------
# Intent-specific strategy instructions — injected based on classification
# -----------------------------------------------------------------------------
_SQL_STRATEGY_BY_INTENT: dict[str, str] = {

    QueryIntent.AGGREGATION: """\
STRATEGY — Aggregation:
- Return a single summary row where possible.
- Use COUNT(*), SUM(), AVG(), MIN(), MAX() as appropriate.
- If multiple metrics are requested, use scalar subqueries or a single SELECT
  with multiple aggregate expressions.
- Do NOT return raw rows when the user wants a summary.
""",

    QueryIntent.TREND: """\
STRATEGY — Time Series Trend:
- Identify the time dimension column (created_at, date, timestamp, month, etc.).
- Truncate/group by the appropriate time grain:
    DATE_TRUNC('month', col) for monthly
    DATE_TRUNC('week',  col) for weekly
    DATE_TRUNC('day',   col) for daily
- Always alias the truncated time column (e.g., AS month, AS week, AS day).
- ORDER BY the time dimension ASC — this is mandatory for trend queries.
- Remove the default LIMIT or set it to a large value (e.g., 10000) since
  trend data needs all time points.
""",

    QueryIntent.COMPARISON: """\
STRATEGY — Comparison:
- If comparing time periods: use FILTER(WHERE ...) with conditional aggregation.
  Example:
    SUM(amount) FILTER (WHERE date_trunc('month', created_at) = date_trunc('month', CURRENT_DATE))     AS this_month,
    SUM(amount) FILTER (WHERE date_trunc('month', created_at) = date_trunc('month', CURRENT_DATE - INTERVAL '1 month')) AS last_month
- If comparing categories: GROUP BY the category column, ORDER BY metric DESC.
- If comparing entities (A vs B): use CASE WHEN or a UNION if schemas differ.
- Always include both sides of the comparison in the result set.
""",

    QueryIntent.RANKING: """\
STRATEGY — Ranking:
- Use ORDER BY <metric> DESC (or ASC for bottom-N).
- Apply LIMIT to the N requested. If N not specified, default to 10.
- GROUP BY the entity being ranked before ordering.
- If the user wants the ranked list alongside a total, use scalar subqueries:
    SELECT
      (SELECT COUNT(*) FROM entity_table) AS total_count,
      (SELECT ARRAY_AGG(name ORDER BY metric DESC) 
       FROM (SELECT name, SUM(value) AS metric FROM ... GROUP BY name LIMIT N) sub
      ) AS top_names;
""",

    QueryIntent.DISTRIBUTION: """\
STRATEGY — Distribution:
- GROUP BY the category column.
- Include both the category label and the numeric value (count, sum, etc.).
- ORDER BY the numeric value DESC unless alphabetical order is implied.
- For pie/bar chart suitability: ensure exactly 2 columns — label and value.
- Alias columns meaningfully: AS category, AS total, AS percentage, etc.
""",

    QueryIntent.LOOKUP: """\
STRATEGY — Lookup / Filter:
- Apply WHERE clauses using the user's filter criteria.
- For string matching: use ILIKE and TRIM to handle case/whitespace:
    TRIM(column_name) ILIKE '%value%'
- For date filtering: use BETWEEN or >= / <= with explicit date casting.
- Return relevant columns for the entity, not just IDs.
- Apply LIMIT 100 unless user asks for all records.
""",

    QueryIntent.DRILL_DOWN: """\
STRATEGY — Drill-Down:
- The user is following up on a previous result. Use conversation history to
  identify WHICH entity or time period they want to drill into.
- Apply that as a WHERE filter on top of the previous query's logic.
- Return detail-level columns (not aggregates) unless they ask for a sub-summary.
- Reference the previous question's context to infer the implicit filter.
""",

    QueryIntent.UNKNOWN: """\
STRATEGY — Unknown Intent:
- Make your best effort to produce a correct SELECT statement.
- Default to returning a representative sample (LIMIT 100).
- If genuinely ambiguous, prefer aggregation over raw row dumps.
""",
}

# -----------------------------------------------------------------------------
# Safety patterns for names / time references
# -----------------------------------------------------------------------------
_SQL_RULES_SAFETY = """\
SAFETY PATTERNS:
- String filters:  TRIM(col) ILIKE '%value%'
- Current month:   DATE_TRUNC('month', CURRENT_DATE)
- Last month:      DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
- This year:       DATE_PART('year', col) = DATE_PART('year', CURRENT_DATE)
- Null safety:     Use COALESCE(col, 0) for numeric columns used in aggregation.
- Division safety: Use NULLIF(denominator, 0) to prevent divide-by-zero.
- ARRAY_AGG with ORDER: ARRAY_AGG(col ORDER BY other_col DESC)

FORBIDDEN PATTERNS:
- No correlated subqueries in SELECT that return >1 row.
- No UNION unless schemas genuinely differ.
- No window functions without an OVER() clause.
- No hardcoded schema names (public.) unless schema_text shows them.
"""


def build_sql_messages(
    *,
    question: str,
    schema_text: str,
    strategy: str,
    business_notes: str,
    history: list[ChatTurn],
) -> list[ChatMessage]:
    """
    Stage 2: Generate a PostgreSQL SELECT statement from natural language.
    """
    strategy_block = _SQL_STRATEGY_BY_INTENT.get(strategy, _SQL_STRATEGY_BY_INTENT[QueryIntent.UNKNOWN])

    system_content = (
        "You are a senior PostgreSQL analyst. Your sole output is a single "
        "read-only SQL SELECT statement.\n\n"
        + _SQL_RULES_CORE
        + "\n"
        + strategy_block
        + "\n"
        + _SQL_RULES_SAFETY
    )

    history_block = ""
    if history:
        rendered = "\n".join(f"  {t.role.upper()}: {t.content}" for t in history[-6:])
        history_block = f"\n\nConversation history:\n{rendered}"

    user_prompt = (
        f"Database schema:\n{schema_text}\n"
        f"Business notes: {business_notes}\n"
        f"{history_block}\n\n"
        f"User question: {question}\n\n"
        "Return ONLY the SQL statement."
    )

    return [
        ChatMessage(role="system", content=system_content),
        ChatMessage(role="user", content=user_prompt),
    ]


# =============================================================================
# STAGE 3 — Chart Intelligence Prompt
# =============================================================================

CHART_SYSTEM_PROMPT = """\
You are a Data Visualization Expert embedded in an analytics assistant.

Your job: given the user's question AND the actual structure of the returned data,
decide whether to show a chart, and if so, which type.

Column Type Taxonomy:
  TEMPORAL  — date, timestamp, year, month, week, day
  NUMERIC   — integer, float, count, sum, total, revenue
  CATEGORY  — string/text with low cardinality (status, name, region)

Chart Selection Rules:
  indicator  → 1 row, 1 or more NUMERIC columns (render as KPI cards)
  line/area  → 1 TEMPORAL + 1 or more NUMERIC columns (trend over time)
  bar        → 1 CATEGORY + 1 NUMERIC (comparison across categories, <20 categories)
  pie        → 1 CATEGORY + 1 NUMERIC, row count ≤ 10
  table      → fallback for everything else
  none       → empty results

Output Rules:
- Return ONLY a valid JSON object.
- Schema:
  {
    "score": <int 0-10>,
    "chart_type": "<indicator|line|area|bar|pie|scatter|heatmap|table|none>",
    "reason": "<one sentence justification>"
  }
"""


def build_chart_intelligence_messages(
    question: str,
    table: TableResult,
) -> list[ChatMessage]:
    """
    Stage 3: Recommend a chart type based on data structure.
    """
    user_prompt = (
        f"User question: {question}\n"
        f"Columns: {table.columns}\n"
        f"Row count: {len(table.rows)}\n\n"
        "Recommend a chart. Return JSON only."
    )

    return [
        ChatMessage(role="system", content=CHART_SYSTEM_PROMPT),
        ChatMessage(role="user", content=user_prompt),
    ]


# =============================================================================
# STAGE 4 — Insight Generation Prompt
# =============================================================================

INSIGHT_SYSTEM_PROMPT = """\
You are a Senior Data Analyst. You MUST be factually accurate.

CRITICAL TRUTH-GATING RULES:
1. ONLY use numbers present in the "Query result data" provided. 
2. NEVER scale, multiply, or "guess" magnitudes. If the data says 10, you must write "10".
3. Cross-check your Headline against the 'pre_computed_stats' before outputting.
4. If the data looks like a sample or is very small, report it exactly as is without assuming it represents a larger population.

Mandatory Analysis Steps:
  1. HEADLINE  — What is the main finding? (Use exact numbers from data).
  2. MAGNITUDE — State absolute values clearly.
  3. PROPORTION — Calculate shares if applicable.
  4. TREND     — State direction of change for time series.

Rules:
  - 3-5 sentences max. No bullet points.
  - Professional, executive tone.
  - Numbers formatted with commas (e.g., 1,250).
  - DO NOT mention "pre_computed_stats", "json", "columns", or internal data labels.
  - DO NOT echo back the input JSON or data structures. Output only the narrative.
  - Do NOT mention SQL or technical terms.
"""


def build_insight_messages(
    question: str,
    table: TableResult,
) -> list[ChatMessage]:
    """
    Stage 4: Generate an analytical narrative.
    """
    user_prompt = (
        f"User question: {question}\n"
        f"Columns: {table.columns}\n"
        f"Data Sample (top 5): {table.rows[:5]}\n\n"
        "Write the analytical summary."
    )

    return [
        ChatMessage(role="system", content=INSIGHT_SYSTEM_PROMPT),
        ChatMessage(role="user", content=user_prompt),
    ]


# =============================================================================
# STAGE 5 — SQL Error Recovery Prompt
# =============================================================================

ERROR_RECOVERY_SYSTEM_PROMPT = """\
You are a PostgreSQL debugging expert. Correct the SQL based on the error.

Output Rules:
- Return ONLY the corrected SQL SELECT statement.
- If unrecoverable, output exactly: -- cannot answer
"""


def build_recovery_messages(
    question: str,
    schema_text: str,
    failed_sql: str,
    error_message: str,
) -> list[ChatMessage]:
    """
    Stage 5: Attempt automatic SQL correction.
    """
    user_prompt = (
        f"Question: {question}\n"
        f"Schema: {schema_text}\n"
        f"Failed SQL: {failed_sql}\n"
        f"Error: {error_message}\n\n"
        "Return fixed SQL."
    )

    return [
        ChatMessage(role="system", content=ERROR_RECOVERY_SYSTEM_PROMPT),
        ChatMessage(role="user", content=user_prompt),
    ]


# =============================================================================
# STAGE 6 — Clarification Request Prompt
# =============================================================================

CLARIFICATION_SYSTEM_PROMPT = """\
You are a helpful analytics assistant. Ask ONE targeted clarifying question.

Rules:
- Be specific about why clarification is needed.
- Suggest 2-3 concrete options.
- Sound like a smart analyst.
"""


def build_clarify_messages(
    question: str,
    schema_text: str,
    reason: str,
) -> list[ChatMessage]:
    """
    Stage 6: Generate a clarifying question.
    """
    user_prompt = (
        f"Question: {question}\n"
        f"Schema Summary: {schema_text}\n"
        f"Constraint: {reason}\n\n"
        "Ask one clarifying question."
    )

    return [
        ChatMessage(role="system", content=CLARIFICATION_SYSTEM_PROMPT),
        ChatMessage(role="user", content=user_prompt),
    ]
