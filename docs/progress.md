# ConnectDB AI — Development Progress Log

Each entry is appended when a milestone is completed.

---

## 2026-04-29 — Project initialized

**Session goal:** Build complete production-quality MVP from scratch.

### Backend completed

| File | Description |
|---|---|
| `backend/requirements.txt` | All Python dependencies pinned |
| `backend/.env.example` | Environment variable template |
| `backend/app/main.py` | FastAPI app factory, CORS, lifespan hook |
| `backend/app/core/config.py` | Pydantic-settings configuration |
| `backend/app/core/errors.py` | Typed error hierarchy + FastAPI exception handlers |
| `backend/app/core/logging.py` | Structured stdout logging |
| `backend/app/schemas/` | Pydantic request/response models (connection, chat, llm) |
| `backend/app/services/session_store.py` | TTL-based in-memory session cache (asyncio-safe) |
| `backend/app/services/pg_connector.py` | asyncpg pool factory with friendly error handling |
| `backend/app/services/schema_inspector.py` | Introspects tables, columns, FKs via information_schema |
| `backend/app/services/sql_guard.py` | sqlglot AST validation — rejects all non-SELECT statements |
| `backend/app/services/sql_executor.py` | Safe execution: READ ONLY transaction, statement_timeout, row coercion |
| `backend/app/services/analyzer.py` | Heuristic chart-type selection → Plotly JSON spec |
| `backend/app/services/chat_orchestrator.py` | Full NL → SQL → execute → analyse pipeline |
| `backend/app/llm/base.py` | Abstract LLMProvider interface |
| `backend/app/llm/openai_provider.py` | OpenAI adapter (list_models + chat) |
| `backend/app/llm/gemini_provider.py` | Google Gemini adapter |
| `backend/app/llm/anthropic_provider.py` | Anthropic Claude adapter |
| `backend/app/llm/prompts.py` | SQL-generation and insight-generation prompt templates |
| `backend/app/llm/factory.py` | Provider factory by name |
| `backend/app/api/routes/connections.py` | POST /api/connections/test + /connect |
| `backend/app/api/routes/sessions.py` | GET schema, PUT notes, DELETE session |
| `backend/app/api/routes/llm.py` | GET /api/llm/models |
| `backend/app/api/routes/chat.py` | POST /api/chat/{id}/message |
| `backend/tests/test_sql_guard.py` | 14 tests covering all SQL injection / DDL / DML scenarios |

### Frontend completed

| File | Description |
|---|---|
| `frontend/package.json` | Next.js 14, Tailwind, Zustand, react-plotly.js, lucide-react |
| `frontend/tsconfig.json` | TypeScript strict mode |
| `frontend/tailwind.config.ts` | Dark-theme custom color palette |
| `frontend/next.config.mjs` | Plotly SSR exclusion |
| `frontend/src/app/globals.css` | Base styles + scrollbar customization |
| `frontend/src/app/layout.tsx` | Root layout with metadata |
| `frontend/src/app/page.tsx` | Main page — sidebar + chat |
| `frontend/src/store/sessionStore.ts` | Zustand store: session, AI config, messages, notes |
| `frontend/src/lib/types.ts` | TypeScript types mirroring backend schemas |
| `frontend/src/lib/api.ts` | Typed fetch wrapper for all backend endpoints |
| `frontend/src/components/ui/Button.tsx` | Primary / secondary / ghost button |
| `frontend/src/components/ui/Input.tsx` | Labelled text input |
| `frontend/src/components/ui/Select.tsx` | Labelled select dropdown |
| `frontend/src/components/ui/Card.tsx` | Titled section card |
| `frontend/src/components/Sidebar/ConnectionForm.tsx` | Postgres credentials + Test/Connect buttons |
| `frontend/src/components/Sidebar/AIConfigPanel.tsx` | Provider + API key + model dropdown |
| `frontend/src/components/Sidebar/BusinessNotesPanel.tsx` | Business definitions textarea (auto-saved) |
| `frontend/src/components/Sidebar/Sidebar.tsx` | Left sidebar wrapper + schema table list |
| `frontend/src/components/Chat/LoadingDots.tsx` | Animated 3-dot loading indicator |
| `frontend/src/components/Chat/Message.tsx` | Renders user / assistant / error / loading messages |
| `frontend/src/components/Chat/MessageList.tsx` | Scrollable message feed with auto-scroll |
| `frontend/src/components/Chat/ChatInput.tsx` | Text area + Send button, Enter-to-send |
| `frontend/src/components/Chat/ChatContainer.tsx` | Main content area = MessageList + ChatInput |
| `frontend/src/components/Renderers/ChartRenderer.tsx` | Plotly chart (client-only, dynamic import) |
| `frontend/src/components/Renderers/TableRenderer.tsx` | Paginated data table |
| `frontend/src/components/Renderers/SqlBlock.tsx` | Collapsible SQL display with copy button |

### Scripts + config

| File | Description |
|---|---|
| `.gitignore` | Python + Node + editor ignores |
| `start-back.sh`, `.ps1`, `.bat` | One-click launchers for backend (cross-platform) |
| `start-front.sh`, `.ps1`, `.bat` | One-click launchers for frontend (cross-platform) |
| `Readme.md` | Full usage documentation and project overview |

---

## Next steps / ideas for post-MVP

- Streaming chat responses (Server-Sent Events) for faster perceived response
- Vanna-style example retrieval: store past Q+SQL pairs as few-shot examples
- Export to CSV / Excel
- Multi-database support (MySQL, SQLite, BigQuery)
- Persistent sessions via Redis
- Authentication (NextAuth.js)

---

## 2026-05-02 — Type Alignment and Documentation

**Session goal:** Resolve TypeScript type safety issues and provide comprehensive system documentation.

### Fixes & Improvements

| Area | Description |
|---|---|
| `frontend/src/components/Chat/ChatInput.tsx` | Fixed type mismatch by updating fallback payload to include `classification`, `explanation`, and `needs_clarification`. |
| `frontend/.eslintrc.json` | Added ESLint configuration for consistent linting. |
| `docs/instruction.md` | Created comprehensive system setup and running instructions. |

### Tasks Completed

- [x] Align frontend `ChatResponse` fallback with backend v2.0.0 schema.
- [x] Verify frontend type safety via ESLint.
- [x] Document system prerequisites and run instructions.
- [x] Document recent major work in instruction log.

---

## 2026-05-09 — Codebase Standardization & TypeScript Fixes

**Session goal:** Bring the project into compliance with global rules for documentation, file headers, and project structure, while resolving critical TypeScript errors.

### Fixes & Improvements

| Area | Description |
|---|---|
| `frontend/src/global.d.ts` | Created global declaration for `plotly.js-dist-min` to resolve missing type definition errors. |
| `frontend/src/components/ui/Card.tsx` | Fixed incompatible `title` property override by using `Omit<HTMLAttributes<HTMLDivElement>, 'title'>`. |
| `docs/` | Commenced rebranding of `instruction.md` to `instructions.md` and creation of `project_overview.md`. |
| All Files | Starting systematic update of mandatory file summary blocks and function-level comments. |

### Tasks Completed

- [x] Resolve `plotly.js-dist-min` TypeScript declaration error.
- [x] Resolve `Card.tsx` property conflict error.
- [x] Add mandatory header blocks to `Card.tsx` and `global.d.ts`.
- [x] Rename `docs/instruction.md` to `docs/instructions.md` and standardize content.
- [x] Create `docs/project_overview.md`.
- [x] Apply mandatory summary blocks and comments to all files (Phase 1: Backend Core).
- [x] Apply mandatory summary blocks and comments to all files (Phase 2: Frontend Core).
- [x] Update documentation at `docs/instructions.md` and `docs/project_overview.md`.
- [x] Update `docs/instructions.md` with Quick Start scripts and automated launchers.
- [x] Mark automation scripts and `Readme.md` as completed in progress log.


