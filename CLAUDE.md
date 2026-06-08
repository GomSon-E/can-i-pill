# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**이거뭐약** — 약(약물) + 영양제 + 음식 상호작용 리스크 탐지 AI 웹앱

A web application that analyzes drug-food-supplement interactions using AI to help users identify potential health risks when taking medications with certain foods or supplements.

### Tech Stack
- **Frontend**: React 19 + TypeScript + Vite
- **Backend**: FastAPI + Python
- **Database**: Supabase (PostgreSQL)
- **AI/APIs**: Gemini API, Data.go.kr API
- **Testing**: Vitest (frontend), pytest (backend)

---

## Development Workflow

### Development Commands

**Frontend** (run from `/frontend`):
```bash
npm run dev      # Start Vite dev server (http://localhost:5173)
npm run build    # Build for production
npm run test     # Run all tests with Vitest
npm test -- [filename]  # Run specific test file
npm run lint     # Run ESLint
```

**Backend** (run from root with venv activated):
```bash
python -m pytest              # Run all backend tests
python -m pytest tests/test_health.py  # Run specific test file
python -m pytest -v           # Verbose output
python -m pytest -k test_name # Run by test name pattern
uvicorn app.main:app --reload # Start FastAPI server (http://localhost:8000)
```

### Development Setup
1. Frontend: `npm install` in `/frontend`
2. Backend: `python -m pip install -r backend/requirements.txt`
3. Environment: Copy `.env` file with API keys (Supabase, Gemini, data.go.kr)
4. Run both servers: frontend on 5173, backend on 8000 (frontend proxies to backend via Vite config)

---

## Project Structure

### Frontend (`/frontend`)
- **src/pages/** — Screen components organized by onboarding flow
  - `intro/` — Introduction screens (INTRO-01, INTRO-02, INTRO-03)
  - `ob/` — Onboarding screens (OB-01 through OB-05)
  - `sub/` — Main app screens (health analysis, history)
- **src/components/** — Reusable UI components (StatusBar, etc.)
- **src/store/** — State management (Zustand-like stores for OCR, analysis)
- **src/tests/** — Vitest test files (one per page/flow)
- **src/AppRoutes.tsx** — React Router configuration
- **vite.config.ts** — Vite config with API proxy to backend on `/ocr`, `/analyze`, `/user`, `/health`, `/prescriptions`, `/supplements`, `/history`

### Backend (`/backend`)
- **app/main.py** — FastAPI app entry point, router registration
- **app/routers/** — API endpoint modules
  - `health.py` — Health condition endpoints
  - `user.py` — User profile endpoints
  - `prescriptions.py` — Prescription text extraction
  - `supplements.py` — Supplement information
  - `history.py` — User history
  - `mock_ai.py` — Mock AI endpoints for OCR/analysis
- **app/db.py** — Supabase database connection
- **app/store.py** — In-memory/session storage
- **tests/** — pytest test files mirroring routers

### Data & Docs
- **data/** — Seed data tables (interaction data, supplement info)
- **docs/v2/** — Architecture docs and test reports
- **scripts/** — Utilities (e.g., md_to_docx.py for report generation)

---

## Development Practices

### TDD (Test-Driven Development)
This project uses **strict TDD**. See `plan.md` for the master checklist.

When asked "go":
1. Find the next unchecked item in `plan.md`
2. Write a failing test first
3. Implement only code to make the test pass
4. Mark item as complete in `plan.md`

**Never** skip the test-first step; always follow the plan exactly.

### API Proxying
Frontend Vite dev server proxies backend API calls:
- `/ocr`, `/label`, `/analyze` — Image analysis endpoints
- `/user`, `/health-info` — User data
- `/prescriptions`, `/supplements`, `/history` — Drug/supplement info

Vite proxy is configured in `vite.config.ts` to route to `http://localhost:8000`.

### Environment Variables
Required in `.env`:
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY` — Database
- `GEMINI_API_KEY` — AI analysis
- `DATA_GO_KR_API_KEY` — Korean drug database API

---

## Key Architectural Patterns

### Backend Router Pattern
Each API module is a standalone router registered in `main.py`:
```python
app.include_router(user.router)
app.include_router(health_router.router)
# etc.
```
Modular: adding an endpoint means adding a new route in the relevant router, not touching main.py.

### Frontend State Management
Separate stores for different concerns:
- `ocrStore` — OCR results & image state
- `analyzeStore` — Interaction analysis results

Lightweight, not Redux-scale. Update as needed for new flows.

### Testing Patterns
- **Frontend**: Vitest + React Testing Library. Test user interactions, not implementation.
- **Backend**: pytest fixtures for FastAPI TestClient. Mock Supabase for unit tests; use real DB for integration.

---

## Common Tasks

**Add a new backend endpoint:**
1. Create a test in `backend/tests/test_<router_name>.py`
2. Add the route in `backend/app/routers/<router_name>.py`
3. Register in `app/main.py` if it's a new router

**Add a new frontend page:**
1. Create component in `src/pages/<section>/<PageName>.tsx`
2. Add route in `AppRoutes.tsx`
3. Create test in `src/tests/<page_name>.test.tsx`
4. Test user flow before marking done

**Update interaction data:**
- Seed data is in `/data/interaction_seed_table.md`
- Load into Supabase via admin scripts or direct SQL

---

## Debugging Notes

- **CORS issues?** Check Vite proxy config; ensure backend server is running.
- **Supabase connection fails?** Verify `.env` keys and network access to `gcdfiekzbbjfpvjtzitd.supabase.co`.
- **Tests fail randomly?** Check for state leakage; each test should be independent. Reset stores/mocks.
- **Frontend doesn't reflect backend changes?** Ensure backend server restarted and frontend Vite proxy is active.

---

## Global Instructions Override

- **Commits**: Never include `Co-Authored-By:` trailers. Use the `commit-msg` skill to generate messages.
- **TDD strict mode**: Always follow `plan.md` and test-first discipline.
