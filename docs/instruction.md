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
