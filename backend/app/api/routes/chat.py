"""
File: chat.py
Version: 1.1.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: API Routes for the chat interface. Handles message submission, 
             session-based context retrieval, and AI orchestration triggers.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_session
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_orchestrator import handle_message
from app.services.session_store import Session

# Initialize router
router = APIRouter()


@router.post("/{session_id}/message", response_model=ChatResponse)
async def post_message(
    request: ChatRequest,
    session: Session = Depends(get_session),
) -> ChatResponse:
    """
    Main entry point for natural language database queries.
    
    Processing Steps:
    1. Validates the session exists via dependency injection.
    2. Passes the question and AI configuration to the Chat Orchestrator.
    3. Returns the full pipeline result (SQL + Data + Visualization + Insights).
    
    Args:
        request: The user's question and model preferences.
        session: The active session (automatically injected).
        
    Returns:
        A ChatResponse containing the analytical result.
    """
    return await handle_message(
        session, 
        question=request.question, 
        ai_config=request.ai_config
    )
