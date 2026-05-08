"""
File: connections.py
Version: 1.1.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: API Routes for database connection management. Provides endpoints for 
             testing credentials and establishing long-lived sessions with 
             automated schema introspection.
"""

from fastapi import APIRouter

from app.core.errors import ConnectDBError
from app.schemas.connection import (
    ConnectResponse,
    PostgresCredentials,
    TestConnectionResponse,
)
from app.services import pg_connector, schema_inspector
from app.services.session_store import session_store

# Initialize router
router = APIRouter()


@router.post("/test", response_model=TestConnectionResponse)
async def test_connection(creds: PostgresCredentials) -> TestConnectionResponse:
    """
    Lightweight connectivity check.
    Attempts to connect to the database and retrieve the server version without 
    creating a persistent session or pool.
    
    Args:
        creds: Database host, port, user, password, and dbname.
        
    Returns:
        A boolean status and optional server version or error hint.
    """
    try:
        version = await pg_connector.test_connection(creds)
        return TestConnectionResponse(ok=True, server_version=version)
    except ConnectDBError as e:
        return TestConnectionResponse(ok=False, error=e.hint)


@router.post("/connect", response_model=ConnectResponse)
async def connect(creds: PostgresCredentials) -> ConnectResponse:
    """
    Establishes a persistent database session.
    
    Processing Steps:
    1. Creates a managed asyncpg connection pool.
    2. Runs the Schema Inspector to cache table and relationship metadata.
    3. Registers the pool and schema in the Session Store.
    
    Args:
        creds: Database host, port, user, password, and dbname.
        
    Returns:
        The generated session_id and the initial schema summary.
    """
    pool = await pg_connector.create_pool(creds)
    try:
        schema = await schema_inspector.introspect(pool, schemas=creds.schemas)
    except Exception:
        # Prevent connection leaks if introspection fails
        await pool.close()
        raise
    
    session = await session_store.create(pool=pool, schema=schema)
    return ConnectResponse(session_id=session.id, schema_summary=schema)
