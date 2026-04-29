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
    configure_logging()
    yield
    await session_store.shutdown()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="ConnectDB AI",
        version="0.1.0",
        description="AI-powered analytics assistant for PostgreSQL.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(connections.router, prefix="/api/connections", tags=["connections"])
    app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
    app.include_router(llm.router, prefix="/api/llm", tags=["llm"])
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
