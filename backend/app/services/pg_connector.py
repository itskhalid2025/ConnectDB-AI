import asyncio
import logging

import asyncpg

from app.core.errors import ConnectionFailed
from app.schemas.connection import PostgresCredentials

log = logging.getLogger(__name__)

CONNECT_TIMEOUT = 10.0


def _to_dsn_kwargs(creds: PostgresCredentials) -> dict[str, object]:
    return {
        "host": creds.host,
        "port": creds.port,
        "database": creds.database,
        "user": creds.user,
        "password": creds.password,
        "ssl": creds.sslmode if creds.sslmode != "disable" else False,
    }


async def test_connection(creds: PostgresCredentials) -> str:
    """Open one connection, run SELECT 1, return server version."""
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
        await conn.fetchval("SELECT 1")
        version = await conn.fetchval("SHOW server_version")
        return str(version)
    finally:
        await conn.close()


async def create_pool(creds: PostgresCredentials) -> asyncpg.Pool:
    """Create a small read-oriented pool. Raises ConnectionFailed on failure."""
    try:
        pool = await asyncio.wait_for(
            asyncpg.create_pool(
                **_to_dsn_kwargs(creds),
                min_size=1,
                max_size=4,
                command_timeout=30,
            ),
            timeout=CONNECT_TIMEOUT,
        )
    except (asyncio.TimeoutError, OSError, asyncpg.PostgresError) as e:
        raise ConnectionFailed(f"Could not open pool: {e}", hint="Verify the connection details.") from e

    if pool is None:
        raise ConnectionFailed("Pool initialization returned None.")
    return pool
