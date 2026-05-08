"""
File: schema_inspector.py
Version: 1.1.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: Database introspection engine. Queries PostgreSQL system catalogs to build a 
             structured representation of tables, columns, and foreign keys, then formats 
             them for the LLM context window.
"""

import asyncpg
import logging
from app.schemas.connection import ColumnInfo, ForeignKey, SchemaSummary, TableInfo

# Initialize logger
log = logging.getLogger(__name__)

# Built-in Postgres schemas we always exclude — only user data is interesting for analysis.
SYSTEM_SCHEMAS = ("pg_catalog", "information_schema", "pg_toast")

# --- Optimized Metadata Queries ---

# Fetch all user tables and views
_TABLES_QUERY = """
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_type IN ('BASE TABLE', 'VIEW')
  AND ($1::text[] IS NULL OR table_schema = ANY($1::text[]))
  AND table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
ORDER BY table_schema, table_name
"""

# Fetch column details including data types and nullability
_COLUMNS_QUERY = """
SELECT table_schema, table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE ($1::text[] IS NULL OR table_schema = ANY($1::text[]))
  AND table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
ORDER BY table_schema, table_name, ordinal_position
"""

# Fetch foreign key relationships for join inference
_FK_QUERY = """
SELECT
    tc.table_schema,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS references_table,
    ccu.column_name AS references_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND ($1::text[] IS NULL OR tc.table_schema = ANY($1::text[]))
  AND tc.table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
"""

# Fetch approximate row counts for query optimization hints
_ROWCOUNT_QUERY = """
SELECT n.nspname AS schema, c.relname AS name, c.reltuples::bigint AS approx
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind IN ('r', 'p')
  AND ($1::text[] IS NULL OR n.nspname = ANY($1::text[]))
  AND n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
"""


async def introspect(pool: asyncpg.Pool, schemas: list[str] | None = None) -> SchemaSummary:
    """
    Scans the connected database and returns a structured summary.
    
    Args:
        pool: The asyncpg connection pool.
        schemas: Optional list of schemas to filter by.
        
    Returns:
        A SchemaSummary object containing all table and relationship metadata.
    """
    async with pool.acquire() as conn:
        tables_rows = await conn.fetch(_TABLES_QUERY, schemas)
        cols_rows = await conn.fetch(_COLUMNS_QUERY, schemas)
        fk_rows = await conn.fetch(_FK_QUERY, schemas)
        rowcount_rows = await conn.fetch(_ROWCOUNT_QUERY, schemas)

    # Group columns by table
    cols_by_table: dict[tuple[str, str], list[ColumnInfo]] = {}
    for r in cols_rows:
        key = (r["table_schema"], r["table_name"])
        cols_by_table.setdefault(key, []).append(
            ColumnInfo(
                name=r["column_name"],
                data_type=r["data_type"],
                is_nullable=r["is_nullable"] == "YES",
            )
        )

    # Group foreign keys by table
    fks_by_table: dict[tuple[str, str], list[ForeignKey]] = {}
    for r in fk_rows:
        key = (r["table_schema"], r["table_name"])
        fks_by_table.setdefault(key, []).append(
            ForeignKey(
                column=r["column_name"],
                references_table=r["references_table"],
                references_column=r["references_column"],
            )
        )

    # Map approximate row counts
    rowcounts: dict[tuple[str, str], int] = {
        (r["schema"], r["name"]): int(r["approx"]) if r["approx"] is not None else 0
        for r in rowcount_rows
    }

    # Build final TableInfo list
    tables: list[TableInfo] = []
    for r in tables_rows:
        key = (r["table_schema"], r["table_name"])
        tables.append(
            TableInfo(
                schema=r["table_schema"],
                name=r["table_name"],
                columns=cols_by_table.get(key, []),
                foreign_keys=fks_by_table.get(key, []),
                approx_row_count=rowcounts.get(key),
            )
        )

    return SchemaSummary(tables=tables)


def render_schema_for_prompt(summary: SchemaSummary) -> str:
    """
    Generates a compact textual representation of the schema.
    Optimized for LLM context economy while preserving all relationship metadata.
    
    Args:
        summary: The SchemaSummary to render.
        
    Returns:
        A string representation of the schema (e.g., "- table(col:type) [FKs: col -> ref]").
    """
    lines: list[str] = []
    for t in summary.tables:
        cols = ", ".join(f"{c.name}:{c.data_type}" for c in t.columns)
        # Note: 'schema_' is used to avoid conflict with protected names in some models
        qualified = f"{t.schema_}.{t.name}" if t.schema_ != "public" else t.name
        line = f"- {qualified}({cols})"
        if t.foreign_keys:
            fks = "; ".join(
                f"{fk.column} -> {fk.references_table}.{fk.references_column}"
                for fk in t.foreign_keys
            )
            line += f"  [FKs: {fks}]"
        lines.append(line)
    
    schema_text = "\n".join(lines) if lines else "(no user tables found)"
    
    # Detailed log for troubleshooting AI hallucinations regarding column names
    log.info("Rendered Schema for Prompt:\n%s", schema_text)
    return schema_text
