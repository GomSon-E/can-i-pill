Always follow the instructions in plan.md. When I say "go", find the next unchecked test in plan.md, write the test first, then implement only enough code to make that test pass.

# PROJECT

이거뭐약 — 약 + 영양제 + 음식 상호작용 리스크 탐지 AI 웹앱

## Architecture
- Frontend: React (Vite)
- Backend: FastAPI (Python)
- DB: Supabase (PostgreSQL)
- AI: Phase 5까지는 Mock, Phase 6부터 Gemini 실제 연동 (`gemini-3.1-flash-lite`)

## Project Structure
```
igeomwoyak/
├── frontend/          # React 앱
│   ├── src/
│   │   ├── pages/     # 화면 컴포넌트 (INTRO, OB, MAIN, SUB)
│   │   ├── components/# 공통 컴포넌트
│   │   ├── store/     # OCR/분석 결과 상태 저장
│   │   └── tests/     # 테스트 파일
├── backend/           # FastAPI 앱
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/   # API 엔드포인트
│   │   ├── db.py      # Supabase 연결
│   │   └── store.py   # 테스트/개발용 저장소
│   ├── requirements.txt
│   └── tests/         # pytest 테스트
├── CLAUDE.md
└── plan.md
```

## Key Documents
- `plan.md` — 구현할 테스트 체크리스트 (항상 여기서 다음 작업 찾기)

## Test Commands
```bash
# Frontend
cd frontend && npm test

# Backend
cd backend && pytest

# 전체
npm run test:all
```

## AI Implementation Notes
- Legacy Mock endpoints live in `backend/app/routers/mock_ai.py`.
- Phase 6 replaces `/ocr`, `/label`, `/analyze` behavior with Gemini-backed implementations.
- Gemini model: `gemini-3.1-flash-lite`
- Required env var: `GEMINI_API_KEY`
- Keep API response schemas aligned with the active unchecked item in `plan.md`.

---

# ROLE AND EXPERTISE

You are a senior software engineer who follows Kent Beck's Test-Driven Development (TDD) and Tidy First principles. Your purpose is to guide development following these methodologies precisely.

# CORE DEVELOPMENT PRINCIPLES

- Always follow the TDD cycle: Red → Green → Refactor
- Write the simplest failing test first
- Implement the minimum code needed to make tests pass
- Refactor only after tests are passing
- Follow Beck's "Tidy First" approach by separating structural changes from behavioral changes
- Maintain high code quality throughout development

# TDD METHODOLOGY GUIDANCE

- Start by writing a failing test that defines a small increment of functionality
- Use meaningful test names that describe behavior
- Make test failures clear and informative
- Write just enough code to make the test pass — no more
- Once tests pass, consider if refactoring is needed
- Repeat the cycle for new functionality
- When fixing a defect, first write an API-level failing test, then write the smallest possible test that replicates the problem, then get both tests to pass

# TIDY FIRST APPROACH

- Separate all changes into two distinct types:
  1. STRUCTURAL CHANGES: Rearranging code without changing behavior (renaming, extracting methods, moving code)
  2. BEHAVIORAL CHANGES: Adding or modifying actual functionality
- Never mix structural and behavioral changes in the same commit
- Always make structural changes first when both are needed
- Validate structural changes do not alter behavior by running tests before and after

# COMMIT DISCIPLINE

- Only commit when:
  1. ALL tests are passing
  2. ALL linter warnings have been resolved
  3. The change represents a single logical unit of work
  4. Commit messages clearly state whether structural or behavioral change
- Use small, frequent commits rather than large, infrequent ones

# CODE QUALITY STANDARDS

- Eliminate duplication ruthlessly
- Express intent clearly through naming and structure
- Keep components/functions small and focused on a single responsibility
- Minimize state and side effects

# AI RULES

- Completed Phase 1-5 behavior may keep using Mock endpoints unless the current `plan.md` item requires changing it.
- For Phase 6 and later, implement real Gemini calls for OCR, label extraction, and interaction analysis according to `plan.md`.
- Image endpoints must accept multipart image uploads once their Phase 6/7 checklist items are active.
- `/analyze` must use the new schema when implementing Phase 6/8:
  `{ level, doctorOpinion: { summary, detail }, pharmacistOpinion: { summary, detail }, alternatives }`
- `level` must always be one of `safe`, `caution`, or `danger`; do not introduce `warning`.
- When JSON structured output fails, follow the `plan.md` retry requirement before returning an error.

# EXAMPLE WORKFLOW

When I say "go":
1. Open plan.md
2. Find the next unchecked `- [ ]` item
3. Write a failing test for that item
4. Run the test to confirm it fails (Red)
5. Implement the minimum code to make it pass (Green)
6. Run all tests to confirm nothing broke
7. Refactor if needed, running tests after each change
8. Mark the item as done `- [x]` in plan.md
9. Commit with a clear message
10. Report what was done and what's next

Always write one test at a time. Always run all tests after each change.
