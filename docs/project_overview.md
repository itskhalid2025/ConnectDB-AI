# Project Overview - ConnectDB AI

## 📅 Created: 2026-05-09 | 12:45 PM
## 📅 Last Updated: 2026-05-09 | 12:45 PM

---

## 🎯 Goal & Required Output
ConnectDB AI is an intelligent data assistant designed to bridge the gap between natural language questions and relational database insights. It allows users to connect to their PostgreSQL databases and ask questions like "What was our revenue last month by category?" and receive:
- The generated SQL query.
- A raw data table of the results.
- An AI-generated insight explaining the data.
- Interactive visualizations (Bar, Line, Pie charts) powered by Plotly.

---

## 👤 Target Users
- **Data Analysts**: Who want to quickly explore data without writing boilerplate SQL.
- **Business Users**: Who need instant answers from their database without waiting for a report.
- **Developers**: Who want to test NL-to-SQL capabilities on their local schemas.

---

## 🛠️ Tech Stack
| Layer | Technology | Reason for Choice |
|---|---|---|
| Frontend | Next.js 14 + TS | Robust routing, server components, and strong type safety. |
| Backend | FastAPI (Python) | High performance, async support, and excellent integration with AI libraries. |
| Database | PostgreSQL | Targeted relational database for this implementation. |
| AI / LLM | Gemini / OpenAI | Multi-provider support for state-of-the-art SQL generation. |
| Styling | Tailwind CSS | Utility-first styling for a premium, custom UI. |
| State | Zustand | Lightweight and performant state management. |

---

## ⚙️ Core Functionalities
### Must Have (MVP)
- [x] Secure database connection testing and persistence (per session).
- [x] Schema introspection (automatic discovery of tables and columns).
- [x] Natural Language to SQL translation with validation.
- [x] Safe SQL execution (Read-only, timeouts).
- [x] Data visualization (Table + Charts).
- [x] Business context injection (Notes to help the LLM understand domain logic).

---

## 🏛️ Architecture & Folder Structure
The project follows a standard decoupled Frontend/Backend architecture.

### Proposed Folder Structure
```
project-root/
├── frontend/
│   ├── src/
│   │   ├── components/ # Atomic UI components and feature-specific renderers
│   │   ├── app/        # Next.js App Router pages and layouts
│   │   ├── store/      # Zustand session management
│   │   └── lib/        # API clients and shared types
├── backend/
│   ├── app/
│   │   ├── api/        # FastAPI routes
│   │   ├── core/       # Config, logging, and error handling
│   │   ├── llm/        # AI provider abstractions and prompts
│   │   ├── schemas/    # Pydantic models for request/response
│   │   └── services/   # Business logic (SQL generation, execution, analysis)
└── docs/               # System documentation and progress logs
```

---

## 💬 Discussion & Decision Log
| Date & Time | Topic | Decision Made | Reason |
|---|---|---|---|
| 2026-05-09 | Documentation | Standardize to Global Rules | Ensure consistency and maintainability across the project. |
| 2026-05-09 | TypeScript | Omit 'title' from HTMLAttributes | Resolved property conflict in Card component. |

---

## ✅ User Approval
- [x] Planning document reviewed by user
- [x] Approved to begin implementation

> Approved by user on: 2026-05-09 | 12:40 PM
> Implementation started on: 2026-05-09 | 12:42 PM
