"""
File: connection.py (Schemas)
Version: 1.1.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: Pydantic models for database connections and introspection. 
             Defines structures for credentials, metadata, and schema summaries.
"""

from pydantic import BaseModel, Field


class PostgresCredentials(BaseModel):
    """Configuration for connecting to a PostgreSQL instance."""
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(default=5432, ge=1, le=65535)
    database: str = Field(..., min_length=1, max_length=128)
    user: str = Field(..., min_length=1, max_length=128)
    password: str = Field(default="", max_length=512)
    sslmode: str = Field(default="prefer")


class TestConnectionResponse(BaseModel):
    """Result of a lightweight connectivity check."""
    ok: bool
    server_version: str | None = None
    error: str | None = None


class ColumnInfo(BaseModel):
    """Basic metadata for a single database column."""
    name: str
    data_type: str
    is_nullable: bool


class ForeignKey(BaseModel):
    """Describes a relationship between two tables."""
    column: str
    references_table: str
    references_column: str


class TableInfo(BaseModel):
    """
    Detailed metadata for a database table or view.
    Includes columns, relationships, and performance hints.
    """
    schema_: str = Field(alias="schema")
    name: str
    columns: list[ColumnInfo]
    foreign_keys: list[ForeignKey] = Field(default_factory=list)
    approx_row_count: int | None = None

    model_config = {"populate_by_name": True}


class SchemaSummary(BaseModel):
    """The full collection of table metadata for a database."""
    tables: list[TableInfo]


class ConnectResponse(BaseModel):
    """Payload returned after a successful session establishment."""
    session_id: str
    schema_summary: SchemaSummary


class NotesPayload(BaseModel):
    """User-provided business logic notes to guide the AI."""
    notes: str = Field(default="", max_length=10_000)
