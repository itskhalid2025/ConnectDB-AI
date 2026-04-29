"""
File: sql_executor.py
Version: 1.1.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: Safe SQL execution engine. Executes validated queries within read-only 
             PostgreSQL transactions with strict statement-level timeouts. Handles 
             complex PostgreSQL data types by coercing them into JSON-serializable formats.
"""

from __future__ import annotations

import datetime as dt
import decimal
import logging
import uuid
from typing import Any

import asyncpg

from app.core.errors import SQLExecutionError
from app.schemas.chat import TableResult

# Initialize logger
log = logging.getLogger(__name__)


def _coerce(value: Any) -> Any:
    """
    Serializes non-JSON-native PostgreSQL types into standard formats.
    
    Conversions:
    - Decimal -> Float
    - Datetime/Date/Time -> ISO String
    - Timedelta -> Total Seconds (float)
    - UUID -> String
    - Bytes -> Metadata String (e.g., <1024 bytes>)
    
    Args:
        value: The raw value from asyncpg.
        
    Returns:
        A JSON-serializable version of the value.
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat()
    if isinstance(value, dt.timedelta):
        return value.total_seconds()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return f"<{len(bytes(value))} bytes>"
    if isinstance(value, (list, tuple, set)):
        return [_coerce(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _coerce(v) for k, v in value.items()}
    return str(value)


async def execute(
    pool: asyncpg.Pool,
    sql: str,
    *,
    timeout_seconds: int,
    max_rows: int,
) -> TableResult:
    """
    Executes a SQL query against the provided connection pool.
    
    Safety Measures:
    1. Transactional isolation with READ ONLY mode.
    2. LOCAL statement_timeout to prevent hanging queries on the server.
    3. Python-level timeout to prevent hanging connections.
    4. Type coercion to ensure API compatibility.
    
    Args:
        pool: The asyncpg connection pool.
        sql: The validated SQL string to execute.
        timeout_seconds: Hard limit for query execution time.
        max_rows: Maximum number of rows to return (truncation limit).
        
    Returns:
        TableResult containing column names and coerced data rows.
    """
    statement_timeout_ms = timeout_seconds * 1000
    try:
        async with pool.acquire() as conn:
            async with conn.transaction(readonly=True):
                # Apply server-side timeout
                await conn.execute(f"SET LOCAL statement_timeout = {statement_timeout_ms}")
                # Execute with client-side timeout
                records = await conn.fetch(sql, timeout=timeout_seconds)
    except asyncpg.QueryCanceledError as e:
        raise SQLExecutionError(
            f"Query exceeded the {timeout_seconds}s time limit.",
            hint="Try a more specific question or narrow the date range.",
        ) from e
    except asyncpg.ReadOnlySQLTransactionError as e:
        raise SQLExecutionError(
            "The query attempted a write operation.",
            hint="I can only run read queries.",
        ) from e
    except asyncpg.PostgresError as e:
        raise SQLExecutionError(
            f"Database error: {e}",
            hint="The generated SQL ran into an error against your schema — try rephrasing.",
        ) from e

    # Handle empty result sets
    if not records:
        return TableResult(columns=[], rows=[], truncated=False)

    # Standardize result format
    columns = list(records[0].keys())
    truncated = len(records) > max_rows
    use_records = records[:max_rows] if truncated else records
    
    # Map and coerce rows
    rows = [[_coerce(rec[c]) for c in columns] for rec in use_records]
    
    return TableResult(columns=columns, rows=rows, truncated=truncated)
