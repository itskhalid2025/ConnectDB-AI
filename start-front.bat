@echo off
REM Start the Next.js frontend. Runs npm install on first run.
setlocal enabledelayedexpansion

SET SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%frontend"

echo ====================================================
echo   ConnectDB AI - Frontend Startup
echo ====================================================

echo [1/3] ==^> Installing or updating Node.js dependencies...
call npm install
if !errorlevel! neq 0 (
    echo [ERROR] npm install failed.
    pause
    exit /b !errorlevel!
)

if not exist ".env.local" (
    if exist ".env.local.example" (
        echo [2/3] ==^> No .env.local found - copying from .env.local.example
        copy .env.local.example .env.local
    )
) else (
    echo [2/3] ==^> .env.local file found.
)

echo ====================================================
echo   STATUS: Frontend is ready!
echo   URL:    http://localhost:3000
echo   Press CTRL+C to stop the server.
echo ====================================================
echo [3/3] ==^> Starting Next.js...
call npm run dev

if !errorlevel! neq 0 (
    echo [ERROR] Frontend server exited with error code !errorlevel!.
)

pause
