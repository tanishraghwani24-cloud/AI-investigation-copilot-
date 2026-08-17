# Deployment & Runbook

This document describes how to set up, configure, and run the AI Investigation Copilot from a clean checkout.

## Prerequisites

- **Python**: Version 3.10+ (Recommended 3.11/3.12)
- **Node.js**: Version 18+ (Recommended 20.x)
- **Database**: PostgreSQL 14+ (or a Supabase PostgreSQL instance)
- **API Key**: A valid Google Gemini API Key

## Environment Variables

### Backend Configuration
Create a `.env` file in the `backend/` directory by copying the provided example:
```bash
cp backend/.env.example backend/.env
```
Ensure the following variables are configured in `backend/.env`:
- `APP_NAME`: Set to `"AI Investigation Copilot API"` (default)
- `ENV`: Set to `development` for local execution.
- `DATABASE_URL`: Connection string to your PostgreSQL instance (e.g., `postgresql+asyncpg://postgres:postgres@localhost:5432/investigation_db`). Note that it must use the async `postgresql+asyncpg` driver.
- `GEMINI_API_KEY`: Your Google Gemini API Key.
- `GEMINI_MODEL`: The desired model version (e.g., `gemini-3.5-flash`).

## Setup & Startup

### Database Setup
1. Ensure your PostgreSQL instance is running and the target database (e.g., `investigation_db`) exists.
2. Ensure the `DATABASE_URL` in `backend/.env` points to this database.

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run Alembic migrations to apply the schema to the database:
   ```bash
   alembic upgrade head
   ```
5. Start the backend development server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Next.js development server:
   ```bash
   npm run dev
   ```

## Running the Test Suites

### Backend Unit & Integration Tests
Runs the full suite of agent, API, Mock Bank, and unit tests:
```bash
cd backend
pytest tests -v
```

### Backend E2E Pipeline Tests
Runs the asynchronous end-to-end investigation pipeline covering document upload, reasoning, compliance, decision making, and report generation for various mock bank scenarios (`default`, `high-risk`, `low-risk`, `missing-data`).
```bash
cd backend
pytest tests/e2e/test_full_pipeline.py -v
```

### Frontend Component Tests
Runs the React/Next.js Jest component tests:
```bash
cd frontend
npm run test
```

## Known Limitations & Assumptions

- **Mocked DB in E2E Tests**: The E2E tests use an in-memory mocked DB and document repository instead of real PostgreSQL, to allow testing without requiring an active database instance.
- **Static Scenarios**: The pipeline trigger utilizes fixed `MockBankScenario` generation (e.g., `high-risk`, `low-risk`) with deterministic seeds, so multiple executions of the same scenario locally will result in identically named case outputs (`CASE-2025-00042-*`).
- **File System Uploads**: Document uploads are temporarily saved to a local `uploads/` directory on the backend filesystem. A production deployment would require an integration with cloud storage like S3 or GCS.
- **Async Execution**: The pipeline is orchestrated via FastAPI's `BackgroundTasks`, which handles pipeline execution async. Make sure your server doesn't shut down before background tasks complete if running locally.
