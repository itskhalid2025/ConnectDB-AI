"""Safe SQL execution against the user's Postgres pool.

Runs every query in a READ ONLY transaction with a per-statement timeout,
and converts asyncpg Records into JSON-serialisable rows for the API layer.
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

log = logging.getLogger(__name__)


def _coerce(value: Any) -> Any:
    """Convert non-JSON-native types into something Pydantic can serialise."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, decimal.Decimal):
        # Decimals come back from numeric columns; cast to float for JSON.
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
    """Execute `sql` read-only and return a TableResult.

    The timeout is enforced both at the asyncpg client level (`timeout=`) and
    at the server level (`SET LOCAL statement_timeout`). The transaction is
    READ ONLY so even if the guard somehow missed a write op, the server
    would reject it.
    """
    statement_timeout_ms = timeout_seconds * 1000
    try:
        async with pool.acquire() as conn:
            async with conn.transaction(readonly=True):
                await conn.execute(f"SET LOCAL statement_timeout = {statement_timeout_ms}")
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

    if not records:
        return TableResult(columns=[], rows=[], truncated=False)

    columns = list(records[0].keys())
    truncated = len(records) > max_rows
    use_records = records[:max_rows] if truncated else records
    rows = [[_coerce(rec[c]) for c in columns] for rec in use_records]
    return TableResult(columns=columns, rows=rows, truncated=truncated)
