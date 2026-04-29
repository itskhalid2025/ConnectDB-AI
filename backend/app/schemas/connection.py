from pydantic import BaseModel, Field


class PostgresCredentials(BaseModel):
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(default=5432, ge=1, le=65535)
    database: str = Field(..., min_length=1, max_length=128)
    user: str = Field(..., min_length=1, max_length=128)
    password: str = Field(default="", max_length=512)
    sslmode: str = Field(default="prefer")


class TestConnectionResponse(BaseModel):
    ok: bool
    server_version: str | None = None
    error: str | None = None


class ColumnInfo(BaseModel):
    name: str
    data_type: str
    is_nullable: bool


class ForeignKey(BaseModel):
    column: str
    references_table: str
    references_column: str


class TableInfo(BaseModel):
    schema_: str = Field(alias="schema")
    name: str
    columns: list[ColumnInfo]
    foreign_keys: list[ForeignKey] = Field(default_factory=list)
    approx_row_count: int | None = None

    model_config = {"populate_by_name": True}


class SchemaSummary(BaseModel):
    tables: list[TableInfo]


class ConnectResponse(BaseModel):
    session_id: str
    schema_summary: SchemaSummary


class NotesPayload(BaseModel):
    notes: str = Field(default="", max_length=10_000)
