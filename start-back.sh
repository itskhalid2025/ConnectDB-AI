#!/usr/bin/env bash
# Start the FastAPI backend. Creates a venv on first run.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend"

if [ ! -d ".venv" ]; then
  echo "==> Creating virtual environment"
  python -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate

echo "==> Installing dependencies (idempotent)"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  echo "==> No .env found — copying from .env.example"
  cp .env.example .env
fi

echo "==> Starting FastAPI on http://localhost:8000"
exec uvicorn app.main:app --reload --port 8000
