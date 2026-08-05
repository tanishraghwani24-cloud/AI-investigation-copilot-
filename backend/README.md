# AI Investigation Copilot

An enterprise-grade AI-powered copilot that assists fraud analysts in investigating financial fraud cases. The system helps analysts collect evidence, generate hypotheses, validate compliance, and produce explainable investigation reports.

> **Current Phase: Phase 0 — Project Scaffolding**
>
> This project is being developed incrementally. This repository currently represents the foundational backend scaffold. Business logic, AI agents, database integration, and investigation workflows will be introduced in subsequent phases.

---

## Tech Stack

- **Framework:** FastAPI
- **Language:** Python 3.12+
- **Settings:** pydantic-settings

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── api/routes/           # API route handlers
│   ├── core/                 # Application configuration
│   ├── agents/               # AI agents (future)
│   ├── graph/                # LangGraph workflow (future)
│   ├── models/               # Database models (future)
│   ├── schemas/              # Pydantic schemas (future)
│   ├── db/                   # Database connection (future)
│   └── utils/                # Utility functions (future)
├── tests/                    # Test suite
├── logs/                     # Application logs
├── .env.example              # Environment variable template
├── requirements.txt          # Python dependencies
└── README.md
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repository-url>
cd backend
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Set up environment variables

```bash
cp .env.example .env
```

---

## Run the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### Verify

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "ai-investigation-copilot"
}
```

API documentation is auto-generated at:

- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`

---

## Development Phases

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 0** | Project Scaffolding | ✅ Complete |
| Phase 1 | Database & Core Models | 🔲 Planned |
| Phase 2 | AI Agents & LangGraph Workflow | 🔲 Planned |
| Phase 3 | Evidence & Compliance Validation | 🔲 Planned |
| Phase 4 | Decision Optimization & Reporting | 🔲 Planned |
