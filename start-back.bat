@echo off
REM Start the FastAPI backend. Creates a venv on first run.
setlocal enabledelayedexpansion

SET SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%backend"

echo ====================================================
echo   ConnectDB AI - Backend Startup
echo ====================================================

if not exist ".venv" (
    echo [1/4] ==^> Creating virtual environment...
    python -m venv .venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b !errorlevel!
    )
) else (
    echo [1/4] ==^> Virtual environment already exists.
)

echo [2/4] ==^> Activating virtual environment...
call .venv\Scripts\activate.bat

echo [3/4] ==^> Installing or updating dependencies...
python -m pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
if !errorlevel! neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b !errorlevel!
)

if not exist ".env" (
    if exist ".env.example" (
        echo [4/4] ==^> No .env found - copying from .env.example
        copy .env.example .env
    )
) else (
    echo [4/4] ==^> .env file found.
)

echo ====================================================
echo   STATUS: Backend is ready!
echo   URL:    http://localhost:8000
echo   Press CTRL+C to stop the server.
echo ====================================================
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

if !errorlevel! neq 0 (
    echo [ERROR] Backend server exited with error code !errorlevel!.
)

pause
