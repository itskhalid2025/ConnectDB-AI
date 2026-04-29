from fastapi import APIRouter, Depends, Path

from app.api.deps import get_session
from app.schemas.connection import NotesPayload, SchemaSummary
from app.services.session_store import Session, session_store

router = APIRouter()


@router.get("/{session_id}/schema", response_model=SchemaSummary)
async def get_schema(session: Session = Depends(get_session)) -> SchemaSummary:
    return session.schema


@router.put("/{session_id}/notes")
async def update_notes(
    payload: NotesPayload,
    session: Session = Depends(get_session),
) -> dict[str, bool]:
    session.notes = payload.notes
    return {"ok": True}


@router.delete("/{session_id}")
async def delete_session(
    session_id: str = Path(..., min_length=8, max_length=64),
) -> dict[str, bool]:
    await session_store.delete(session_id)
    return {"ok": True}
