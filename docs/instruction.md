# System Instructions - ConnectDB AI

## Overview
ConnectDB AI is an intelligent analytical interface that allows users to query PostgreSQL databases using natural language. It leverages a multi-stage AI pipeline to classify intent, generate SQL, and provide insights with visualizations.

## How to Run the System

### Prerequisites
- Node.js (v18+)
- Python (v3.10+)
- PostgreSQL instance

### Backend Setup
1. Navigate to the `backend` directory.
2. Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Configure environment variables in `.env`.
5. Run the server using the provided script or uvicorn:
   ```powershell
   uvicorn app.main:app --reload
   ```

### Frontend Setup
1. Navigate to the `frontend` directory.
2. Install dependencies:
   ```powershell
   npm install
   ```
3. Run the development server:
   ```powershell
   npm run dev
   ```

---

## Work Log

### 2026-05-02 00:10 AM
- **Issue**: TypeScript type mismatch in `ChatInput.tsx`. The fallback error payload was missing `classification`, `explanation`, and `needs_clarification` fields required by the `ChatResponse` interface (v2.0.0).
- **Fix**: Updated `ChatInput.tsx` to include the missing fields in the `catch` block payload.
- **Validation**: Added `.eslintrc.json` to frontend and ran `npm run lint` to verify type safety.
- **Files Modified**:
  - `frontend/src/components/Chat/ChatInput.tsx`
  - `frontend/.eslintrc.json` (New)
  - `docs/instruction.md` (New)

### 2026-05-02 01:20 AM
- **Feature**: Multi-Tenant Schema Scoping.
- **Problem**: In databases with many schemas (e.g. one per tenant), the AI context window would overflow if all schemas were introspected.
- **Solution**: Added "Target Schemas" field to connection credentials.
- **Implementation**:
  - Backend: Updated `schema_inspector.py` to filter metadata by a provided `schemas` list.
  - Backend: Updated `PostgresCredentials` schema and `/connect` route.
  - Frontend: Added "Target Schemas" input to `ConnectionForm.tsx`.
  - Frontend: Updated session store and types to handle the new field.
- **Files Modified**:
  - `backend/app/schemas/connection.py`
  - `backend/app/services/schema_inspector.py`
  - `backend/app/api/routes/connections.py`
  - `frontend/src/lib/types.ts`
  - `frontend/src/store/sessionStore.ts`
  - `frontend/src/components/Sidebar/ConnectionForm.tsx`
  - `Readme.md`

### 2026-05-08 12:26 AM
- **Issue**: CORS Preflight Failure. Requests from `http://localhost:3000` were blocked by the backend because the preflight `OPTIONS` request lacked the `Access-Control-Allow-Origin` header.
- **Fix**: 
  - Updated `backend/.env` to include `http://127.0.0.1:3000` in `CORS_ORIGINS`.
  - Updated `backend/app/main.py` to enable `allow_credentials=True` in `CORSMiddleware`.
- **Validation**: Verified `CORSMiddleware` configuration and settings parsing.
- **Files Modified**:
  - `backend/.env`
  - `backend/app/main.py`
  - `docs/instruction.md`

### 2026-05-08 01:40 AM
- **Issue**: AI pipeline failures caused by Gemini truncation (responses cut off mid-sentence).
- **Fix**: 
  - Implemented **JSON Mode** for Gemini provider to eliminate markdown clutter and save tokens.
  - Relaxed **Safety Filters** to prevent over-eager blocking of valid SQL code.
  - Switched to **Stateless Generation** (`generate_content`) for better stability in pipeline calls.
  - Created robust **JSON/SQL Extraction** utilities in `llm_utils.py` to handle partial responses.
- **Validation**: Updated `query_classifier.py`, `chat_orchestrator.py`, and `sql_guard.py` to use the new hardened extraction logic.
- **Files Modified/Created**:
  - `backend/app/llm/base.py`
  - `backend/app/llm/gemini_provider.py`
  - `backend/app/utils/llm_utils.py` (New)
  - `backend/app/services/query_classifier.py`
  - `backend/app/services/chat_orchestrator.py`
  - `backend/app/services/sql_guard.py`
  - `docs/instruction.md`
