# GitHub Upload Guide

## Step 1: Initialize Git Repository

Open PowerShell in the project root (`C:\dev\tulapramaan`) and run:

```powershell
git init
git branch -M main
```

## Step 2: Add Remote Repository

Replace with your actual GitHub repository URL:

```powershell
git remote add origin https://github.com/harshagauta1902-nelizen/sih_tula_pramaan.git
```

## Step 3: Stage All Files

```powershell
git add .
```

## Step 4: Create Initial Commit

```powershell
git commit -m "Initial commit: TulaPramaan 3-Stage Smart Form System

- FastAPI backend with classification and test plan engines
- React + TypeScript frontend with Vite
- RAG module for clause retrieval
- Demo ML drift risk model
- OIML R76-1:2006 rulepack (DRAFT)
- Comprehensive test suite (129 passed)
- SQLite database for demo
- Full documentation"
```

## Step 5: Push to GitHub

```powershell
git push -u origin main
```

If you get a password prompt, you'll need to use a Personal Access Token (PAT) instead of your password.

## Important Notes

### Files Excluded (by .gitignore)
- `backend/.venv/` - Python virtual environment (users must create their own)
- `frontend/node_modules/` - NPM packages (users must run `npm install`)
- `*.db`, `*.sqlite` - Database files
- `.env` - Environment variables (keep secret keys private!)
- `__pycache__/` - Python cache files
- `frontend/dist/` - Build output

### Files Included (Essential)
- ✅ All source code (`.py`, `.ts`, `.tsx`)
- ✅ Configuration files (`package.json`, `requirements.txt`, etc.)
- ✅ Rulepacks (`rulepacks/oiml-r76-1_2006/*.yaml`)
- ✅ Tests (`backend/tests/*.py`)
- ✅ Documentation (`README.md`, `design.md`, etc.)
- ✅ `.env.example` (template, NOT `.env`)
- ✅ Migration scripts (`backend/migrations/versions/*.py`)

## After Upload: Update README.md

Add these badges at the top of README.md:

```markdown
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
```

## Troubleshooting

### Authentication Failed
Use a Personal Access Token (PAT):
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` scope
3. Use the token as your password when prompted

### Large File Warning
If you get warnings about large files, they're probably in:
- `backend/.venv/` (should be in .gitignore)
- `frontend/node_modules/` (should be in .gitignore)
- Database files (should be in .gitignore)

Run: `git status` to verify only source files are staged.

### Permission Denied
Make sure you have write access to the repository or it's your own repository.

## Quick Verification Commands

Before pushing, verify what will be uploaded:

```powershell
# See all files that will be committed
git status

# See the diff of changes
git diff --cached

# List all tracked files
git ls-files
```

## Post-Upload Checklist

After successful upload:

1. ✅ Verify files on GitHub.com
2. ✅ Update repository description
3. ✅ Add topics/tags: `fastapi`, `react`, `oiml`, `metrology`, `python`, `typescript`
4. ✅ Create a `LICENSE` file (MIT recommended)
5. ✅ Enable GitHub Actions for CI/CD (optional)
6. ✅ Add collaborators if team project

## Clone Instructions (For Team Members)

Add this to your README.md:

```markdown
## Getting Started

### Clone Repository
\`\`\`bash
git clone https://github.com/harshagauta1902-nelizen/sih_tula_pramaan.git
cd sih_tula_pramaan
\`\`\`

### Backend Setup
\`\`\`bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt
\`\`\`

### Frontend Setup
\`\`\`bash
cd frontend
npm install
\`\`\`

### Run Development Servers

Backend:
\`\`\`bash
cd backend
$env:DATABASE_URL="sqlite:///./tulapramaan_demo.db"
.\.venv\Scripts\python.exe -m uvicorn main:app --port 8000 --reload
\`\`\`

Frontend:
\`\`\`bash
cd frontend
npm run dev
\`\`\`

Access:
- Backend API: http://localhost:8000
- Frontend UI: http://localhost:3000
- API Docs: http://localhost:8000/docs
\`\`\`
```
