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

log = logging.getLogger(__name__)


@dataclass
class Session:
    """Per-user session: connection pool + introspected schema + business notes + chat history.

    Sessions are evicted by TTL; the eviction callback closes the underlying pool so
    we don't leak connections to the user's database.
    """

    id: str
    pool: "asyncpg.Pool"
    schema: SchemaSummary
    notes: str = ""
    history: list[ChatTurn] = field(default_factory=list)


class SessionStore:
    def __init__(self) -> None:
        settings = get_settings()
        # maxsize is generous; TTL is what actually bounds memory in practice.
        self._cache: TTLCache[str, Session] = TTLCache(
            maxsize=1024, ttl=settings.session_ttl_seconds
        )
        # Tracks pools we've handed out so that we can close them on eviction
        # even though TTLCache itself has no eviction-callback hook.
        self._lock = asyncio.Lock()

    async def create(self, pool: "asyncpg.Pool", schema: SchemaSummary) -> Session:
        async with self._lock:
            self._sweep()
            session = Session(id=uuid.uuid4().hex, pool=pool, schema=schema)
            self._cache[session.id] = session
            return session

    def get(self, session_id: str) -> Session:
        try:
            return self._cache[session_id]
        except KeyError as exc:
            raise SessionNotFound(
                f"No active session for id={session_id}.",
                hint="Connect to your database again to start a new session.",
            ) from exc

    async def delete(self, session_id: str) -> None:
        async with self._lock:
            session = self._cache.pop(session_id, None)
            if session is not None:
                await self._close_pool(session)

    async def shutdown(self) -> None:
        async with self._lock:
            sessions = list(self._cache.values())
            self._cache.clear()
        for s in sessions:
            await self._close_pool(s)

    @staticmethod
    async def _close_pool(session: Session) -> None:
        try:
            await session.pool.close()
        except Exception as e:  # pragma: no cover — best-effort cleanup
            log.warning("Failed to close pool for session %s: %s", session.id, e)

    def _sweep(self) -> None:
        # TTLCache lazily expires on access; an explicit expire() drops stale
        # sessions so we can close their pools deterministically next call.
        self._cache.expire()


session_store = SessionStore()
