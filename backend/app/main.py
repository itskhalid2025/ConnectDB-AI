"""
File: main.py
Version: 1.1.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: FastAPI Application entry point. Configures the global application state, 
             middleware (CORS), exception handlers, and API route registrations.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat, connections, llm, sessions
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.services.session_store import session_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application lifecycle.
    - Configures logging on startup.
    - Gracefully shuts down the session store and database pools on exit.
    """
    configure_logging()
    yield
    await session_store.shutdown()


def create_app() -> FastAPI:
    """
    Application factory function.
    
    Sets up:
    - FastAPI instance with metadata.
    - CORS middleware for frontend communication.
    - Global exception handlers for ConnectDB errors.
    - Route groups for connections, sessions, LLM, and chat.
    
    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()
    app = FastAPI(
        title="ConnectDB AI",
        version="1.1.0", # Synchronized with our documentation pass
        description="AI-powered analytics assistant for PostgreSQL.",
        lifespan=lifespan,
    )

    # Configure CORS for cross-origin requests from the Next.js frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Register global error interceptors
    register_exception_handlers(app)

    # --- Route Registrations ---
    app.include_router(connections.router, prefix="/api/connections", tags=["connections"])
    app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
    app.include_router(llm.router, prefix="/api/llm", tags=["llm"])
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        """Simple health check endpoint for monitoring."""
        return {"status": "ok"}

    return app


# Instantiate the application
app = create_app()
