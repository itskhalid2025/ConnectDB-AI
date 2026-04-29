# ConnectDB AI

An AI-powered analytics assistant for PostgreSQL databases. Connect your database, ask questions in plain English, and get answers as data tables, charts, and natural-language insights.

---

## What it does

Ask your database questions like you would ask a colleague:

- **\"What is the pass rate?\"** → Insight: \"73% of students passed (marks > 35).\"
- **\"Show monthly sales trend.\"** → Line chart + \"Sales peaked in March (+18% MoM).\"
- **\"Top 10 products by revenue.\"** → Sorted table + bar chart + insight.
- **\"Compare this month vs last month.\"** → Side-by-side bar chart + insight.

Every answer includes the generated SQL in a collapsible block.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Zustand |
| Charts | Plotly.js (react-plotly.js) |
| Backend | FastAPI (Python 3.11+), asyncpg |
| AI providers | OpenAI, Google Gemini, Anthropic Claude |
| SQL safety | sqlglot AST validation + read-only Postgres transactions |
| Database | User-provided PostgreSQL (no internal app database) |

---

## Prerequisites

| Tool | Min version | How to check |
|---|---|---|
| Python | 3.11 | python --version |
| Node.js | 18 | node --version |
| npm | 9 | npm --version |

You also need an API key from one of: OpenAI, Google Gemini, or Anthropic Claude.

---

## Quick start

Open two separate terminal windows.

### Terminal 1 — Backend

**Windows (PowerShell):**

    .\\\\start-back.ps1

**Windows Git Bash / WSL / Mac / Linux:**

    bash start-back.sh

On first run this automatically:
1. Creates backend/.venv/ (Python virtual environment)
2. Installs all Python dependencies
3. Copies backend/.env.example to backend/.env
4. Starts FastAPI at http://localhost:8000

### Terminal 2 — Frontend

**Windows (PowerShell):**

    .\\\\start-front.ps1

**Windows Git Bash / WSL / Mac / Linux:**

    bash start-front.sh

On first run this automatically:
1. Runs npm install
2. Copies frontend/.env.local.example to frontend/.env.local
3. Starts Next.js at http://localhost:3000

Open http://localhost:3000 in your browser.

---

## Step-by-step usage guide

### Step 1 — Connect your PostgreSQL database

Fill in the PostgreSQL connection panel in the left sidebar:

| Field | Example |
|---|---|
| Host | localhost |
| Port | 5432 |
| Database | myapp_db |
| User | postgres |
| Password | your password |

Click Test to verify the credentials without starting a session.
Click Connect to connect. The sidebar shows your tables once connected.

### Step 2 — Configure your AI provider

In the AI provider card:
1. Select a provider: OpenAI, Gemini (Google), or Claude (Anthropic)
2. Paste your API key
3. Click Fetch models — the dropdown populates automatically
4. Select a model (gpt-4o-mini, gemini-1.5-pro, claude-opus-4-7, etc.)

### Step 3 — Add business notes (optional but recommended)

In the Business notes card, define how your domain uses terms:

    \"Pass rate\" = students with marks > 35
    \"Active user\" = logged in within 30 days
    Revenue excludes VAT
    Fiscal year starts in April

These are injected into every query prompt so the AI respects your definitions.

### Step 4 — Ask questions in the chat

Type any question and press Enter or click Send.

**Example questions to try:**
- How many records are in each table?
- What is total revenue this month?
- Show sales by month for the last 6 months.
- Which users signed up most recently?
- Top 5 products by quantity sold.
- Compare revenue: this year vs last year.

**Each response includes:**
1. Plain-English insight (2-3 sentences, specific numbers)
2. Chart — bar, line, or scatter (when data shape supports it)
3. Paginated table (up to 1000 rows, 25 per page)
4. Collapsible SQL block — click \"View generated SQL\" to inspect the query

---

## Manual startup (without the scripts)

**Backend:**

    cd backend
    python -m venv .venv

    # Windows:
    .venv\\\\Scripts\\\\activate
    # Mac / Linux:
    source .venv/bin/activate

    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000

**Frontend:**

    cd frontend
    npm install
    npm run dev

---

## Environment variables

### Backend — backend/.env

Created automatically from backend/.env.example on first run.

| Variable | Default | Description |
|---|---|---|
| CORS_ORIGINS | http://localhost:3000 | Allowed frontend origins |
| MAX_RESULT_ROWS | 1000 | Hard row cap per query |
| QUERY_TIMEOUT_SECONDS | 15 | Server-enforced query timeout |
| SESSION_TTL_SECONDS | 3600 | Session lifetime in seconds |
| CHAT_HISTORY_TURNS | 8 | Past Q&A turns sent to the AI as context |

### Frontend — frontend/.env.local

Created automatically from frontend/.env.local.example on first run.

| Variable | Default | Description |
|---|---|---|
| NEXT_PUBLIC_API_URL | http://localhost:8000 | Backend URL the browser calls |

---

## API reference

Interactive docs: http://localhost:8000/docs (Swagger UI, available while backend runs)

| Method | Endpoint | Purpose |
|---|---|---|
| POST | /api/connections/test | Test credentials without creating a session |
| POST | /api/connections/connect | Connect + inspect schema, returns session_id |
| GET | /api/sessions/{id}/schema | Get introspected schema for a session |
| PUT | /api/sessions/{id}/notes | Save business notes |
| DELETE | /api/sessions/{id} | Close session and release pool |
| GET | /api/llm/models | List models (?provider=openai&api_key=...) |
| POST | /api/chat/{id}/message | Send question, get SQL+table+chart+insight |
| GET | /health | Health check |

---

## Security model

- Only SELECT queries run. sqlglot parses every generated SQL statement. DDL (DROP/ALTER/CREATE), DML (INSERT/UPDATE/DELETE/TRUNCATE), COPY, GRANT — all rejected before execution.
- Read-only transactions. All queries run inside BEGIN READ ONLY — the Postgres server enforces this even if the validator is bypassed.
- Statement timeout. SET LOCAL statement_timeout is applied per query (default 15 seconds).
- Row cap. LIMIT 1000 is injected into queries that are missing one.
- API keys are never stored. They live only in request bodies and are never persisted.
- Sessions are in-memory. They expire after 1 hour of inactivity and are never written to disk.

---

## Running the test suite

    cd backend
    source .venv/bin/activate   # or .venv\\\\Scripts\\\\activate on Windows
    pytest tests/test_sql_guard.py -v

14 tests cover: DROP, DELETE, UPDATE, INSERT, TRUNCATE, ALTER, CREATE, GRANT, multi-statement injection, CTE-with-DML, empty/unparseable input, mixed-case keywords.

---

## Project structure

    ConnectDB-AI/
    |-- README.md
    |-- start-back.sh / .ps1       <- Backend launchers (bash / PowerShell)
    |-- start-front.sh / .ps1      <- Frontend launchers
    |-- docs/
    |   +-- progress.md            <- Development log
    |-- backend/
    |   |-- requirements.txt
    |   +-- app/
    |       |-- main.py            <- FastAPI app + CORS
    |       |-- core/              <- Config, errors, logging
    |       |-- api/routes/        <- Route handlers (4 files)
    |       |-- schemas/           <- Pydantic models
    |       |-- services/
    |       |   |-- sql_guard.py   <- AST SQL safety validation
    |       |   |-- sql_executor.py
    |       |   |-- analyzer.py    <- Chart type heuristics
    |       |   +-- chat_orchestrator.py  <- Full NL->SQL pipeline
    |       |-- llm/               <- OpenAI / Gemini / Anthropic adapters
    |       +-- tests/
    +-- frontend/
        +-- src/
            |-- app/               <- Next.js pages
            |-- components/
            |   |-- Sidebar/       <- Connection + AI config + notes panels
            |   |-- Chat/          <- Message feed + input
            |   |-- Renderers/     <- Chart, table, SQL block
            |   +-- ui/            <- Button, Input, Select, Card
            |-- lib/               <- API client + TypeScript types
            +-- store/             <- Zustand session state

---

## Troubleshooting

**Connection timed out**
Postgres is not running or not reachable. For remote hosts, check firewall rules on the port.

**Authentication failed**
Wrong username or password. Test first with: psql -h HOST -U USER -d DATABASE

**Model dropdown is empty after Fetch models**
The API key is invalid or has extra spaces. Check the provider dashboard.

**No chart appears**
Charts require 2+ columns with a plottable shape. A single value or single text column shows as insight + table only.

**Frontend cannot reach the backend**
Confirm the backend is running on port 8000 and frontend/.env.local contains NEXT_PUBLIC_API_URL=http://localhost:8000.

**PowerShell: \"scripts is disabled\"**
Run once in PowerShell as administrator:
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

---

## Screenshots

Add screenshots here after running the app.

| View | Screenshot |
|---|---|
| Dashboard — connected state | [placeholder] |
| Chat with line chart response | [placeholder] |
