---
inclusion: auto
---

# TulaPramaan Demo Prototype Rules

## Hard Rules (NEVER VIOLATE)

1. **No LLM/ML in Regulatory Decisions**
   - Class determination = deterministic pure function (already implemented)
   - Test applicability = deterministic pure function (already implemented)
   - MPE calculations = deterministic arithmetic
   - ML model is HARDCODED stand-in with fixed weights
   - Label as "demo model" in UI and API responses

2. **RAG Role: Explain Only, Never Decide**
   - RAG cites OIML R 76 clauses
   - RAG explains WHY a classification happened
   - RAG NEVER determines class, test applicability, or pass/fail

3. **Data Precision**
   - Backend: Python Decimal for all calculations
   - API: All numeric values as strings
   - Frontend: Parse strings, display properly

4. **Human Confirmation Required**
   - AMBIGUOUS classification → block until human picks
   - INVALID classification → block until human fixes input
   - Display reason and let human override with logged reason

5. **Draft Labeling**
   - Everything unreviewed shows "DRAFT" badge
   - Test applicability rules marked "VERIFY" show warning
   - Rulepacks not signed off → "DRAFT RULEPACK" label

## Environment Constraints

- **OS**: Windows
- **Python**: 3.12, venv at `backend/.venv`
- **Database**: SQLite (NOT Postgres)
- **Network**: May be down, skip failing downloads
- **Node/npm**: May fail, continue without it if needed

## Scope for Demo Prototype

### IN SCOPE (Priority Order)
1. **Forms** (Stage 1, 1.5, 2, 3 UI components)
2. **RAG Structure** (explain classifications, cite clauses)
3. **Hardcoded ML Model** (fixed weights, demo only)
4. **Wiring** (connect forms to backend APIs)

### OUT OF SCOPE (Do NOT Touch)
- Authentication/authorization
- Audit trail implementation
- OCR/Vision integration
- Report generation
- MPE live feedback calculations
- Playwright tests
- PostgreSQL setup
- Requirements.txt cleanup

## Existing Backend (COMPLETE, Do NOT Modify)

- ✅ Classification engine (pure function)
- ✅ Test plan assembly (pure function)
- ✅ Environment service
- ✅ API routers (23 endpoints)
- ✅ Rulepacks in YAML (rulepacks/oiml-r76-1_2006/)
- ✅ Typed API client (frontend/src/lib/api/)

## Demo Goals

- Record 3-5 minute demo video
- Show full workflow: Stage 1 → 1.5 → 2 → 3
- Demonstrate RAG explaining classifications
- Show "demo model" badge clearly
- Highlight human confirmation for AMBIGUOUS cases
- Display DRAFT labels on unreviewed content

## Tech Stack (Already Set Up)

- Backend: FastAPI + Pydantic + SQLAlchemy + Alembic
- Frontend: React + TypeScript + Vite
- API Client: Axios (typed, complete)
- Database: SQLite (for demo)
