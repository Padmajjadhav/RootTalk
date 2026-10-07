# 🎙️ BhashaLok — Regional Language Preservation Backend API

High-performance, async Python (FastAPI + SQLAlchemy + SQLite) backend engine for the **BhashaLok Marathi Language & Regional Dialect Digital Repository**.

---

## 🚀 Quick Start Guide

### 1. Environment Setup & Installation
```bash
# Navigate to backend directory
cd backend

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 2. Run Database Seeder & Excel Importer
```bash
# Seed 15 Categories, Regional Varieties, and Team Contributors
python database/seed.py

# Import Real Marathi Survey Data from Excel File
python scripts/import_excel.py path/to/your/file.xlsx
```

### 3. Start Backend Server
```bash
# Start FastAPI backend server on http://127.0.0.1:8000
python run_server.py --reload
```

---

## 📘 Interactive API Documentation
- **Swagger UI Interactive Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI Schema**: [http://127.0.0.1:8000/api/v1/openapi.json](http://127.0.0.1:8000/api/v1/openapi.json)

---

## 🧪 Running Automated Tests
```bash
# Run full Pytest test suite
python -m pytest -v
```

---

## 📁 Backend Directory Structure
```
backend/
├── app/
│   ├── api/             # REST Routers (entries, dialects, categories, contributors, voices, analytics)
│   ├── models/          # SQLAlchemy ORM Models (Entry, LanguageVariety, Category, Contributor, VoiceRecording)
│   ├── schemas/         # Pydantic Request/Response DTOs
│   ├── services/        # Phonetic, Audio Waveform & Auth Services
│   ├── database.py      # Database engine & session maker
│   └── main.py          # FastAPI application & middleware
├── database/
│   ├── schema.sql       # SQL table definitions
│   └── seed.py          # Seeder script populating categories & seed data
├── scripts/
│   └── import_excel.py  # Importer script for XLS/XLSX survey datasets
├── uploads/
│   └── audio/           # Physical storage directory for voice recordings
├── tests/
│   └── test_api.py      # Pytest test suite
├── preservation.db      # SQLite database file
├── BACKEND-REPORT.md   # Comprehensive college viva report
└── run_server.py        # Uvicorn server launcher
```
