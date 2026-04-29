from fastapi import APIRouter

from app.core.errors import ConnectDBError
from app.schemas.connection import (
    ConnectResponse,
    PostgresCredentials,
    TestConnectionResponse,
)
from app.services import pg_connector, schema_inspector
from app.services.session_store import session_store

router = APIRouter()


@router.post("/test", response_model=TestConnectionResponse)
async def test_connection(creds: PostgresCredentials) -> TestConnectionResponse:
    try:
        version = await pg_connector.test_connection(creds)
        return TestConnectionResponse(ok=True, server_version=version)
    except ConnectDBError as e:
        return TestConnectionResponse(ok=False, error=e.hint)


@router.post("/connect", response_model=ConnectResponse)
async def connect(creds: PostgresCredentials) -> ConnectResponse:
    pool = await pg_connector.create_pool(creds)
    try:
        schema = await schema_inspector.introspect(pool)
    except Exception:
        await pool.close()
        raise
    session = await session_store.create(pool=pool, schema=schema)
    return ConnectResponse(session_id=session.id, schema_summary=schema)
