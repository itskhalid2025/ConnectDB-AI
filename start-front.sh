#!/usr/bin/env bash
# Start the Next.js frontend. Runs npm install on first run.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/frontend"

if [ ! -d "node_modules" ]; then
  echo "==> Installing Node.js dependencies"
  npm install
fi

if [ ! -f ".env.local" ] && [ -f ".env.local.example" ]; then
  echo "==> No .env.local found — copying from .env.local.example"
  cp .env.local.example .env.local
fi

echo "==> Starting Next.js on http://localhost:3000"
exec npm run dev
