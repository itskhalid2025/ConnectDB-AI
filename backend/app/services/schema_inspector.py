import asyncpg

from app.schemas.connection import ColumnInfo, ForeignKey, SchemaSummary, TableInfo

# Built-in Postgres schemas we always exclude — only user data is interesting.
SYSTEM_SCHEMAS = ("pg_catalog", "information_schema", "pg_toast")

_TABLES_QUERY = """
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_type IN ('BASE TABLE', 'VIEW')
  AND table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
ORDER BY table_schema, table_name
"""

_COLUMNS_QUERY = """
SELECT table_schema, table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
ORDER BY table_schema, table_name, ordinal_position
"""

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
  AND tc.table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
"""

_ROWCOUNT_QUERY = """
SELECT n.nspname AS schema, c.relname AS name, c.reltuples::bigint AS approx
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind IN ('r', 'p')
  AND n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
"""


async def introspect(pool: asyncpg.Pool) -> SchemaSummary:
    async with pool.acquire() as conn:
        tables_rows = await conn.fetch(_TABLES_QUERY)
        cols_rows = await conn.fetch(_COLUMNS_QUERY)
        fk_rows = await conn.fetch(_FK_QUERY)
        rowcount_rows = await conn.fetch(_ROWCOUNT_QUERY)

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

    rowcounts: dict[tuple[str, str], int] = {
        (r["schema"], r["name"]): int(r["approx"]) if r["approx"] is not None else 0
        for r in rowcount_rows
    }

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


import logging
log = logging.getLogger(__name__)

def render_schema_for_prompt(summary: SchemaSummary) -> str:
    """Compact textual representation, optimised for LLM context economy."""
    lines: list[str] = []
    for t in summary.tables:
        cols = ", ".join(f"{c.name}:{c.data_type}" for c in t.columns)
        # Use schema_ correctly from the TableInfo model
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
    log.info("Rendered Schema for Prompt:\n%s", schema_text)
    return schema_text
