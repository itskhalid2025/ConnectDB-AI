from fastapi import APIRouter, Depends

from app.api.deps import get_session
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_orchestrator import handle_message
from app.services.session_store import Session

router = APIRouter()


@router.post("/{session_id}/message", response_model=ChatResponse)
async def post_message(
    request: ChatRequest,
    session: Session = Depends(get_session),
) -> ChatResponse:
    return await handle_message(session, question=request.question, ai_config=request.ai_config)
