# System Instructions - ConnectDB AI

## 1. Prerequisites
- Node.js (v18+)
- Python (v3.10+)
- PostgreSQL instance (v15+)
- Git

## 2. Environment Setup
### Backend
1. Copy `backend/.env.example` to `backend/.env`.
2. Fill in the required environment variables:
   - `DATABASE_URL`: Connection string for your Postgres instance.
   - `OPENAI_API_KEY` / `GEMINI_API_KEY`: Depending on your chosen provider.

### Frontend
1. Copy `frontend/.env.local.example` to `frontend/.env.local`.
2. Ensure `NEXT_PUBLIC_API_URL` points to your backend (default: `http://localhost:8000`).

## 3. Quick Start (Recommended)
You can use the provided start scripts to automate the environment setup and running of the servers.

### Windows (PowerShell/CMD)
- **Backend**: Run `.\start-back.ps1` or `start-back.bat`
- **Frontend**: Run `.\start-front.ps1` or `start-front.bat`

### Linux/macOS (Bash)
- **Backend**: Run `./start-back.sh`
- **Frontend**: Run `./start-front.sh`

## 4. Manual Installation & Running
### Backend (FastAPI)
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
4. Run the server:
   ```powershell
   uvicorn app.main:app --reload
   ```

### Frontend (Next.js)
1. Navigate to the `frontend` directory.
2. Install dependencies:
   ```powershell
   npm install
   ```
3. Run the development server:
   ```powershell
   npm run dev
   ```

## 4. Running Tests
### Backend
```powershell
cd backend
pytest
```

## 5. Building for Production
### Frontend
```powershell
cd frontend
npm run build
```

## 6. Work Log (Maintenance)
### 2026-05-09
- Renamed `instruction.md` to `instructions.md`.
- Standardized documentation to follow global rules.
- Fixed TypeScript errors in `Card.tsx` and `global.d.ts`.
- Implemented mandatory file summary headers across core files.
- Added "Quick Start" section with `.bat`, `.ps1`, and `.sh` scripts.

