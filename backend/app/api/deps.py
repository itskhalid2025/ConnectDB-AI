from fastapi import Path

from app.services.session_store import Session, session_store


def get_session(session_id: str = Path(..., min_length=8, max_length=64)) -> Session:
    return session_store.get(session_id)
