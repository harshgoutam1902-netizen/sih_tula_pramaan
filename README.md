# TulaPramaan — 3-Stage Smart Form System
### AI-Assisted OIML R 76 Type Evaluation & Test Report Automation Suite

## Overview

This is a guided, three-stage form flow system that transforms the complex OIML R 76 type evaluation process into a streamlined workflow:

1. **Stage 1**: Instrument parameter collection (e, Max, category parameters)
2. **Stage 1.5**: Deterministic classification routing (AI explains, never decides)
3. **Stage 2**: Class-specific test execution with live feedback
4. **Stage 3**: Environment capture with auto-propagation

**Core Principle**: The AI layer never decides class, test applicability, MPE, or pass/fail. A deterministic rules engine does. AI only assists with OCR, prose generation, and explanations.

---

## Project Structure

```
sih project/
├── backend/
│   ├── models/
│   │   ├── rulepacks.py         # Classification & test applicability rules
│   │   ├── instrument.py        # Instrument profiles & classification results
│   │   └── test_plan.py         # Dynamic test plan models
│   ├── services/
│   │   ├── classification_engine.py  # Pure function: determine_class()
│   │   └── test_plan_engine.py       # Pure function: assemble_test_plan()
│   ├── tests/
│   │   ├── test_classification.py          # Unit tests
│   │   ├── test_classification_properties.py  # Property-based tests (Hypothesis)
│   │   └── test_test_plan_assembly.py      # Test plan assembly tests
│   ├── migrations/
│   │   └── versions/
│   │       └── 001_add_3stage_form_tables.py  # Initial schema
│   ├── config.py                # Application settings (Pydantic)
│   ├── database.py              # Database session management
│   ├── requirements.txt         # Production dependencies
│   └── requirements-dev.txt     # Development dependencies
│
├── rulepacks/
│   └── oiml-r76-1_2006/
│       ├── classification.yaml       # Table 3 (class bands) + Table 4 (ratios)
│       ├── test_applicability.yaml   # Annex A/B test matrix
│       ├── README.md                 # Rulepack documentation
│       └── REVIEW_CHECKLIST.md       # Metrologist sign-off template
│
├── frontend/                    # (To be implemented)
│
├── .env.example                 # Environment variable template
├── requirements.md              # Functional & non-functional requirements
├── design.md                    # Technical architecture & data models
├── tasks.md                     # Implementation task breakdown
├── IMPLEMENTATION_PROGRESS.md   # Current progress tracking
└── README.md                    # This file
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Node.js 18+ (for frontend, when implemented)

### 1. Environment Setup

```bash
# Clone repository (if applicable)
cd "sih project"

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# CRITICAL: Change SECRET_KEY and JWT_SECRET_KEY in production
# Configure DATABASE_URL for your PostgreSQL instance
```

### 3. Database Setup

```bash
# Create database
createdb tulapramaan

# Run migrations
alembic upgrade head

# Verify tables created
psql tulapramaan -c "\dt"
```

### 4. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=services --cov=models --cov-report=html

# Run property-based tests (1000+ examples)
pytest tests/test_classification_properties.py -v

# Run specific test file
pytest tests/test_classification.py -v
```

### 5. Start Development Server

```bash
# From backend directory
uvicorn main:app --reload --port 8000

# API documentation available at:
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

---

## Development Workflow

### Adding a New Feature

1. **Read the design document** (`design.md`) to understand architecture
2. **Check tasks.md** for relevant task
3. **Write tests first** (TDD approach)
4. **Implement feature** following existing patterns
5. **Run tests** to verify
6. **Update IMPLEMENTATION_PROGRESS.md**

### Running Specific Test Suites

```bash
# Classification engine tests
pytest tests/test_classification*.py -v

# Test plan assembly tests
pytest tests/test_test_plan*.py -v

# Property-based tests only (slow, comprehensive)
pytest tests/test_classification_properties.py -v --hypothesis-show-statistics
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history
```

### Code Quality

```bash
# Format code
black backend/

# Sort imports
isort backend/

# Type checking
mypy backend/

# Linting
flake8 backend/
pylint backend/
```

---

## Key Features

### ✅ Implemented (Phase 1-3 Core)

- **Deterministic Classification Engine**
  - Pure function: `determine_class(e, max_cap, rulepack)`
  - DETERMINED / AMBIGUOUS / INVALID status handling
  - Decimal precision throughout (no float errors)
  - 1000+ property-based test cases (Hypothesis)

- **Test Plan Assembly Engine**
  - Pure function: `assemble_test_plan(instrument, class, rulepack)`
  - Conditional test applicability (25 tests defined)
  - Variant resolution (discrimination, tilting)
  - Security-hardened condition evaluator

- **Versioned Rulepacks**
  - OIML R 76-1:2006 classification rules (YAML)
  - Test applicability matrix from Annex A/B
  - Version pinning per job (immutable)
  - In-memory caching for performance

- **Database Schema**
  - Extended `instrument_profiles` table
  - `class_determinations` with audit trail
  - `test_plans` with resolved tests
  - `environment_sessions` and `environment_readings`

### 🚧 In Progress

- API endpoints (FastAPI routes)
- Frontend components (React + TypeScript)
- Environment auto-propagation service
- Integration with existing OCR/Vision features

### 📋 Pending

- Metrologist review of test applicability matrix (BLOCKER for production)
- End-to-end integration tests
- Frontend Stage 1-3 UI components
- Report generation integration
- Pilot testing with technicians

---

## Testing Philosophy

### Property-Based Testing (Hypothesis)

The classification engine uses property-based testing to verify correctness across thousands of random inputs:

```python
@given(e=decimal_e_strategy(), max_cap=decimal_max_strategy())
@settings(max_examples=1000)
def test_classification_always_returns_valid_status(e, max_cap, rulepack):
    """Property: Classification always returns one of three valid statuses."""
    result = determine_class(e, max_cap, rulepack)
    assert result.status in ["DETERMINED", "AMBIGUOUS", "INVALID"]
```

This catches edge cases that manual test cases would miss.

### Unit Tests

Boundary cases and known scenarios are covered by traditional unit tests:

- Class II lower bound: e=0.001g, n=100
- Class II upper bound: e=0.05g, n=100,000
- Ambiguous classifications at band boundaries
- Invalid configurations (e=0, negative values)

---

## Architecture Principles

1. **Rules as Data, Not Code**
   - All OIML R 76 rules stored in versioned YAML files
   - Code interprets data, never hardcodes thresholds

2. **Pure Function Core**
   - Classification and test plan logic are pure functions
   - No I/O, no database queries, no LLM calls
   - Fully unit-testable and deterministic

3. **Human-in-the-Loop**
   - System detects ambiguity, never auto-resolves
   - All overrides logged to audit trail
   - Explicit confirmation required for edge cases

4. **Decimal Precision**
   - Python `Decimal` type throughout
   - No floating-point rounding errors in MPE calculations

---

## Configuration

See `.env.example` for all available configuration options. Key settings:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/tulapramaan

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key

# Rulepack
RULEPACK_DIR=./rulepacks
DEFAULT_RULEPACK_VERSION=R76-1:2006

# AI/OCR (if enabled)
OPENAI_API_KEY=your-openai-api-key

# Feature Flags
FEATURE_OCR_ENABLED=true
FEATURE_LIVE_MPE_FEEDBACK=true
```

---

## Contributing

### Code Style

- Follow PEP 8
- Use type hints on all functions
- Write docstrings with examples
- Keep functions pure where possible
- Add tests for new features

### Commit Messages

```
feat: Add classification API endpoint
fix: Handle zero e values in classification
test: Add property tests for multi-interval validation
docs: Update README with testing instructions
```

---

## Documentation

- **requirements.md**: Functional and non-functional requirements
- **design.md**: Technical architecture, data models, API specs
- **tasks.md**: Task breakdown with dependencies and estimates
- **IMPLEMENTATION_PROGRESS.md**: Current status and next steps

---

## License

[To be determined]

---

## Contact

[To be determined]

---

## Acknowledgments

- OIML R 76-1:2006 and R 76-2:2006 standards
- International Organization of Legal Metrology (OIML)

---

**Status**: Phase 1-3 core logic complete. API endpoints and frontend in progress.

See `IMPLEMENTATION_PROGRESS.md` for detailed status.
