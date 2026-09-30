# Getting Started with TulaPramaan 3-Stage Smart Form System

This guide will walk you through setting up the development environment and running the application for the first time.

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11 or higher** - [Download](https://www.python.org/downloads/)
- **PostgreSQL 14 or higher** - [Download](https://www.postgresql.org/download/)
- **Git** (optional, for version control)
- **Node.js 18+** (for frontend, when implemented)

### Verify Installations

```bash
python --version    # Should show 3.11 or higher
psql --version      # Should show 14 or higher
pip --version       # Should be installed with Python
```

---

## Step 1: Clone or Navigate to Project

```bash
cd "c:\Users\user\OneDrive\Desktop\sih project"
```

---

## Step 2: Set Up Python Virtual Environment

### Windows (CMD)
```cmd
python -m venv venv
venv\Scripts\activate
```

### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Linux/Mac
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your command prompt.

---

## Step 3: Install Dependencies

```bash
cd backend

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (optional but recommended)
pip install -r requirements-dev.txt

# Verify installation
pip list
```

Expected key packages:
- fastapi
- uvicorn
- sqlalchemy
- alembic
- pydantic
- pytest
- hypothesis

---

## Step 4: Configure Environment Variables

```bash
# Copy the example environment file
copy .env.example .env  # Windows CMD
# OR
cp .env.example .env    # Linux/Mac/PowerShell

# Edit .env with your settings
notepad .env  # Windows
# OR
nano .env     # Linux/Mac
```

### Critical Settings to Update

```env
# Database - Update with your PostgreSQL credentials
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/tulapramaan

# Security - MUST CHANGE in production
SECRET_KEY=your-random-secret-key-minimum-32-characters-long
JWT_SECRET_KEY=your-random-jwt-secret-key-also-32-chars-min

# OpenAI (if using OCR features)
OPENAI_API_KEY=your-openai-api-key-here
```

### Generate Secure Keys (Python)

```python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Run this twice to generate both SECRET_KEY and JWT_SECRET_KEY.

---

## Step 5: Set Up PostgreSQL Database

### Option A: Using psql Command Line

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE tulapramaan;

# Create user (optional, if not using postgres user)
CREATE USER tulapramaan_user WITH PASSWORD 'your_secure_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE tulapramaan TO tulapramaan_user;

# Exit psql
\q
```

### Option B: Using pgAdmin

1. Open pgAdmin
2. Right-click "Databases" → "Create" → "Database"
3. Name: `tulapramaan`
4. Save

### Verify Database Connection

```bash
# Update .env with correct DATABASE_URL, then test:
python -c "from sqlalchemy import create_engine; import os; from dotenv import load_dotenv; load_dotenv(); engine = create_engine(os.getenv('DATABASE_URL')); conn = engine.connect(); print('✓ Database connection successful'); conn.close()"
```

---

## Step 6: Run Database Migrations

```bash
# From backend directory
cd backend

# Initialize Alembic (if not done)
alembic revision --autogenerate -m "Initial migration"

# Run migrations
alembic upgrade head

# Verify tables created
psql -U postgres -d tulapramaan -c "\dt"
```

Expected tables:
- `instrument_profiles`
- `class_determinations`
- `test_plans`
- `environment_sessions`
- `environment_readings`
- `alembic_version`

---

## Step 7: Verify Rulepack Loading

```bash
# From backend directory
python -c "from models.rulepacks import load_rulepack; classification, test_app = load_rulepack('R76-1:2006'); print(f'✓ Loaded {len(classification.class_bands)} class bands'); print(f'✓ Loaded {len(test_app.tests)} tests')"
```

Expected output:
```
✓ Loaded 6 class bands
✓ Loaded 25 tests
```

---

## Step 8: Run Tests

```bash
# From backend directory
cd backend

# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=services --cov=models --cov-report=html

# View coverage report (generated in htmlcov/index.html)
# Open htmlcov/index.html in browser

# Run only fast unit tests
pytest tests/ -m unit -v

# Run property-based tests (slow, 1000+ examples)
pytest tests/test_classification_properties.py -v --hypothesis-show-statistics
```

Expected results:
- All tests should pass ✓
- Coverage should be >90% for services and models

---

## Step 9: Start Development Server

```bash
# From backend directory
python main.py

# OR using uvicorn directly
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## Step 10: Test the API

### Using Browser

1. Open: http://localhost:8000
   - Should show app info

2. Open: http://localhost:8000/docs
   - Interactive API documentation (Swagger UI)

3. Open: http://localhost:8000/redoc
   - Alternative API documentation (ReDoc)

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# API status
curl http://localhost:8000/api/v1/status

# Expected response:
{
  "status": "operational",
  "version": "1.0.0",
  "environment": "development",
  "features": {
    "ocr_enabled": true,
    "live_mpe_feedback": true,
    ...
  }
}
```

---

## Common Issues and Solutions

### Issue: ModuleNotFoundError

**Solution**: Ensure virtual environment is activated and dependencies installed
```bash
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Issue: Database connection error

**Solution**: Check DATABASE_URL in .env
```bash
# Test connection
psql -U postgres -d tulapramaan -c "SELECT 1;"
```

### Issue: Alembic can't find migrations

**Solution**: Ensure you're in backend directory
```bash
cd backend
alembic upgrade head
```

### Issue: ImportError for pydantic_settings

**Solution**: Update pydantic
```bash
pip install --upgrade pydantic pydantic-settings
```

### Issue: Tests fail with "No module named 'backend'"

**Solution**: Set PYTHONPATH
```bash
# Windows CMD
set PYTHONPATH=%CD%

# Windows PowerShell
$env:PYTHONPATH = $PWD

# Linux/Mac
export PYTHONPATH=$PWD
```

---

## Next Steps

### 1. Run the Test Suite

```bash
pytest tests/ -v --cov=services --cov=models
```

### 2. Explore the Rulepacks

```bash
# View classification rules
notepad ..\rulepacks\oiml-r76-1_2006\classification.yaml

# View test applicability matrix
notepad ..\rulepacks\oiml-r76-1_2006\test_applicability.yaml
```

### 3. Try the Classification Engine

Create a test script `test_classification_manual.py`:

```python
from decimal import Decimal
from backend.models.rulepacks import load_rulepack
from backend.services.classification_engine import determine_class

# Load rulepack
classification_rulepack, _ = load_rulepack("R76-1:2006")

# Test classification
e = Decimal("0.001")  # 1mg verification interval
max_cap = Decimal("150")  # 150kg capacity

result = determine_class(e, max_cap, classification_rulepack)

print(f"Status: {result.status}")
print(f"Class: {result.class_}")
print(f"Computed n: {result.computed_n}")
```

Run it:
```bash
python test_classification_manual.py
```

### 4. Review Documentation

- **requirements.md**: Functional requirements
- **design.md**: Architecture and data models
- **tasks.md**: Implementation task breakdown
- **IMPLEMENTATION_PROGRESS.md**: Current status

### 5. Start Implementing API Endpoints

See tasks.md, Phase 2:
- T2.8: POST /classification/determine
- T2.9: POST /classification/confirm
- T3.6: POST /test-plans/assemble

---

## Development Workflow

### Making Changes

1. **Create a branch** (if using Git)
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write tests first** (TDD)
   ```bash
   # Create test file
   tests/test_your_feature.py
   
   # Run tests (they should fail)
   pytest tests/test_your_feature.py -v
   ```

3. **Implement feature**
   ```bash
   # Edit code
   backend/services/your_feature.py
   ```

4. **Run tests** (they should pass now)
   ```bash
   pytest tests/test_your_feature.py -v
   ```

5. **Check code quality**
   ```bash
   black backend/
   flake8 backend/
   mypy backend/
   ```

6. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: Add your feature description"
   ```

---

## Useful Commands Reference

```bash
# Database
alembic upgrade head              # Apply all migrations
alembic downgrade -1              # Rollback last migration
alembic history                   # View migration history
psql -U postgres -d tulapramaan   # Connect to database

# Testing
pytest tests/ -v                  # Run all tests
pytest tests/ -k test_name        # Run specific test
pytest tests/ -x                  # Stop on first failure
pytest tests/ --lf                # Re-run last failed tests
pytest tests/ --pdb               # Drop into debugger on failure

# Code Quality
black backend/                    # Format code
isort backend/                    # Sort imports
flake8 backend/                   # Lint code
mypy backend/                     # Type check

# Server
python main.py                    # Start server
uvicorn main:app --reload         # Start with auto-reload
uvicorn main:app --port 8001      # Start on different port
```

---

## Getting Help

1. **Check IMPLEMENTATION_PROGRESS.md** for current status
2. **Review design.md** for architecture decisions
3. **Check tasks.md** for task dependencies
4. **Read inline code comments** for implementation details

---

## Ready to Code!

You're all set! The core classification and test plan engines are implemented and tested. Next steps are:

1. ✓ Backend core logic complete
2. → Implement API endpoints
3. → Integrate with existing features (once you provide details)
4. → Build frontend components

See **IMPLEMENTATION_PROGRESS.md** for detailed status.
