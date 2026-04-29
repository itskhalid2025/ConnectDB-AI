"""
File: pg_connector.py
Version: 1.1.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: PostgreSQL connectivity module. Handles low-level connection logic, 
             authentication error mapping, and asynchronous connection pool management 
             using asyncpg.
"""

import asyncio
import logging
import asyncpg

from app.core.errors import ConnectionFailed
from app.schemas.connection import PostgresCredentials

# Initialize logger
log = logging.getLogger(__name__)

# Connection safety timeout
CONNECT_TIMEOUT = 10.0


def _to_dsn_kwargs(creds: PostgresCredentials) -> dict[str, object]:
    """Maps Pydantic credentials model to asyncpg-compatible arguments."""
    return {
        "host": creds.host,
        "port": creds.port,
        "database": creds.database,
        "user": creds.user,
        "password": creds.password,
        "ssl": creds.sslmode if creds.sslmode != "disable" else False,
    }


async def test_connection(creds: PostgresCredentials) -> str:
    """
    Validates database credentials by opening a single ephemeral connection.
    
    Args:
        creds: The connection credentials to test.
        
    Returns:
        The server version string (e.g., "15.3").
        
    Raises:
        ConnectionFailed: With descriptive hints for auth, network, or DB existence errors.
    """
    try:
        conn = await asyncio.wait_for(
            asyncpg.connect(**_to_dsn_kwargs(creds)), timeout=CONNECT_TIMEOUT
        )
    except asyncio.TimeoutError as e:
        raise ConnectionFailed(
            "Connection timed out.",
            hint="Check that the host and port are reachable from this machine.",
        ) from e
    except (asyncpg.InvalidPasswordError, asyncpg.InvalidAuthorizationSpecificationError) as e:
        raise ConnectionFailed("Authentication failed.", hint="Check the username and password.") from e
    except asyncpg.InvalidCatalogNameError as e:
        raise ConnectionFailed(
            f"Database '{creds.database}' does not exist.",
            hint="Verify the database name.",
        ) from e
    except (OSError, asyncpg.PostgresError) as e:
        raise ConnectionFailed(f"Could not connect: {e}", hint="Check host, port, and network access.") from e

    try:
        # Basic validation query
        await conn.fetchval("SELECT 1")
        version = await conn.fetchval("SHOW server_version")
        return str(version)
    finally:
        await conn.close()


async def create_pool(creds: PostgresCredentials) -> asyncpg.Pool:
    """
    Creates a managed connection pool for the session.
    Pool size is kept small to conserve server-side resources while 
    supporting concurrent analytical queries.
    
    Args:
        creds: The connection credentials.
        
    Returns:
        An initialized asyncpg.Pool.
        
    Raises:
        ConnectionFailed: If the pool fails to initialize within the timeout.
    """
    try:
        pool = await asyncio.wait_for(
            asyncpg.create_pool(
                **_to_dsn_kwargs(creds),
                min_size=1,
                max_size=4, # Analytical workloads rarely benefit from massive pools
                command_timeout=30,
            ),
            timeout=CONNECT_TIMEOUT,
        )
    except (asyncio.TimeoutError, OSError, asyncpg.PostgresError) as e:
        raise ConnectionFailed(f"Could not open pool: {e}", hint="Verify the connection details.") from e

    if pool is None:
        raise ConnectionFailed("Pool initialization returned None.")
    return pool
