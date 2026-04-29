"""
File: sessions.py
Version: 1.1.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: API Routes for session management. Handles metadata retrieval, 
             business context (notes) updates, and explicit session termination.
"""

from fastapi import APIRouter, Depends, Path

from app.api.deps import get_session
from app.schemas.connection import NotesPayload, SchemaSummary
from app.services.session_store import Session, session_store

# Initialize router
router = APIRouter()


@router.get("/{session_id}/schema", response_model=SchemaSummary)
async def get_schema(session: Session = Depends(get_session)) -> SchemaSummary:
    """
    Retrieves the cached schema summary for the active session.
    Used by the frontend to populate the sidebar table explorer.
    """
    return session.schema


@router.put("/{session_id}/notes")
async def update_notes(
    payload: NotesPayload,
    session: Session = Depends(get_session),
) -> dict[str, bool]:
    """
    Updates the business context notes for the session.
    These notes are injected into the SQL generation prompt to help 
    the AI understand domain-specific column mappings.
    """
    session.notes = payload.notes
    return {"ok": True}


@router.delete("/{session_id}")
async def delete_session(
    session_id: str = Path(..., min_length=8, max_length=64),
) -> dict[str, bool]:
    """
    Terminates the session and immediately closes all associated database connections.
    """
    await session_store.delete(session_id)
    return {"ok": True}
