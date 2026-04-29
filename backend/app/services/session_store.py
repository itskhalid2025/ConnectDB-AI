"""
File: session_store.py
Version: 1.1.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: In-memory session management service. Stores active database connection 
             pools and chat state. Implements TTL-based eviction to prevent connection 
             leaks and ensure memory efficiency.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from cachetools import TTLCache

from app.core.config import get_settings
from app.core.errors import SessionNotFound
from app.schemas.chat import ChatTurn
from app.schemas.connection import SchemaSummary

if TYPE_CHECKING:
    import asyncpg

# Initialize logger
log = logging.getLogger(__name__)


@dataclass
class Session:
    """
    Represents an active user session with a specific database.
    
    Attributes:
        id: Unique hexadecimal session identifier.
        pool: The dedicated asyncpg connection pool for this database.
        schema: The cached results of database introspection.
        notes: User-provided business context for SQL generation.
        history: Bounded chat history for conversational context.
    """
    id: str
    pool: "asyncpg.Pool"
    schema: SchemaSummary
    notes: str = ""
    history: list[ChatTurn] = field(default_factory=list)


class SessionStore:
    """
    Thread-safe storage for user sessions.
    Uses an LRU/TTL cache to automatically manage session expiration.
    """
    def __init__(self) -> None:
        settings = get_settings()
        # maxsize is a safety cap; TTL is the primary cleanup driver.
        self._cache: TTLCache[str, Session] = TTLCache(
            maxsize=1024, ttl=settings.session_ttl_seconds
        )
        self._lock = asyncio.Lock()

    async def create(self, pool: "asyncpg.Pool", schema: SchemaSummary) -> Session:
        """
        Initializes a new session and stores it in the cache.
        
        Args:
            pool: The initialized asyncpg pool.
            schema: The results of the schema inspector.
            
        Returns:
            The newly created Session object.
        """
        async with self._lock:
            self._sweep() # Remove expired sessions before creating new ones
            session = Session(id=uuid.uuid4().hex, pool=pool, schema=schema)
            self._cache[session.id] = session
            return session

    def get(self, session_id: str) -> Session:
        """
        Retrieves an active session by ID.
        
        Raises:
            SessionNotFound: If the session has expired or never existed.
        """
        try:
            return self._cache[session_id]
        except KeyError as exc:
            raise SessionNotFound(
                f"No active session for id={session_id}.",
                hint="Connect to your database again to start a new session.",
            ) from exc

    async def delete(self, session_id: str) -> None:
        """Explicitly terminates a session and closes its connection pool."""
        async with self._lock:
            session = self._cache.pop(session_id, None)
            if session is not None:
                await self._close_pool(session)

    async def shutdown(self) -> None:
        """Closes all active connection pools on application shutdown."""
        async with self._lock:
            sessions = list(self._cache.values())
            self._cache.clear()
        for s in sessions:
            await self._close_pool(s)

    @staticmethod
    async def _close_pool(session: Session) -> None:
        """Best-effort closure of the asyncpg pool."""
        try:
            await session.pool.close()
        except Exception as e:
            log.warning("Failed to close pool for session %s: %s", session.id, e)

    def _sweep(self) -> None:
        """Triggers the expiration of stale items in the cache."""
        self._cache.expire()


# Singleton instance
session_store = SessionStore()
