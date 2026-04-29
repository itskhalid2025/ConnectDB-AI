from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ConnectDBError(Exception):
    """Base error with a user-safe hint and a stage marker for the chat pipeline."""

    status_code: int = 400
    stage: str = "unknown"

    def __init__(self, message: str, *, hint: str | None = None, stage: str | None = None):
        super().__init__(message)
        self.message = message
        self.hint = hint or message
        if stage:
            self.stage = stage


class ConnectionFailed(ConnectDBError):
    status_code = 400
    stage = "connect"


class SessionNotFound(ConnectDBError):
    status_code = 404
    stage = "session"


class UnsafeSQLError(ConnectDBError):
    """Raised when generated SQL contains a forbidden operation."""

    status_code = 422
    stage = "sql_guard"


class SQLExecutionError(ConnectDBError):
    status_code = 400
    stage = "execute"


class LLMProviderError(ConnectDBError):
    status_code = 502
    stage = "llm"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ConnectDBError)
    async def _handle(request: Request, exc: ConnectDBError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "stage": exc.stage,
                    "message": exc.message,
                    "hint": exc.hint,
                }
            },
        )
