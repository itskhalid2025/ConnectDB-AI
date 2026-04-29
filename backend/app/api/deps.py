"""
File: deps.py
Version: 1.1.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: FastAPI dependency injection providers. Handles shared logic 
             for session retrieval and validation across API routes.
"""

from fastapi import Path
from app.services.session_store import Session, session_store


def get_session(session_id: str = Path(..., min_length=8, max_length=64)) -> Session:
    """
    Dependency provider that retrieves an active session from the session store.
    Used by routes that require a validated database connection and chat context.
    
    Args:
        session_id: The unique session identifier from the URL path.
        
    Returns:
        The active Session object.
        
    Raises:
        SessionNotFound: (via session_store.get) if the session ID is invalid or expired.
    """
    return session_store.get(session_id)
