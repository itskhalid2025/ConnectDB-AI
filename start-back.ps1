# Start the FastAPI backend. Creates a Python venv on first run.
$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location (Join-Path $ScriptDir 'backend')

if (-not (Test-Path '.venv')) {
    Write-Host '==> Creating virtual environment'
    python -m venv .venv
}

Write-Host '==> Activating virtual environment'
& .\.venv\Scripts\Activate.ps1

Write-Host '==> Installing dependencies (idempotent)'
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

if (-not (Test-Path '.env') -and (Test-Path '.env.example')) {
    Write-Host '==> No .env found — copying from .env.example'
    Copy-Item '.env.example' '.env'
}

Write-Host '==> Starting FastAPI on http://localhost:8000'
uvicorn app.main:app --reload --port 8000
