# Mandi Arbitrage Advisor

A full-stack, farmer-centric decision tool that calculates the **true net realization** per quintal across the 5 nearest APMC mandis after factoring in road freight, vehicle capacity, APMC market cess, commission agent fees, and produce quality discounts.

---

## Key Features
- **True Net Profit Comparison**: Eliminates the illusion of high gross prices by computing road freight, statutory mandi fees, and quality cuts.
- **Batched Road Routing**: Computes driving matrix using Google Routes API `computeRouteMatrix` with haversine fallback.
- **Offline Mandi Registry**: Pre-geocoded coordinates for all active APMC mandis in Maharashtra with boundary verification.
- **Daily Price Ingestion**: Cached daily snapshots from data.gov.in with staleness warnings.
- **Precision Financials**: Pure Python `Decimal` arithmetic rounded strictly at output boundaries.
- **Zero-AI Earthy Aesthetic**: "Liquid Glass" styling with high-contrast tactile elements in a palette of forest, wheat, clay, and soil.
- **Bilingual**: English and Hindi toggle with Indian numeral formatting (`en-IN`).

---

## Tech Stack
- **Frontend**: Next.js 14+ (App Router, TypeScript), Tailwind CSS, next-themes, Recharts, Lucide React, Vitest.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic, HTTPX, SlowAPI.
- **Databases**: SQLite (`aiosqlite`) for local development, PostgreSQL (`asyncpg`) for production.

---

## Prerequisites
- **Python**: 3.11 or higher
- **Node.js**: v18.18 or higher (v20+ recommended)
- **PowerShell**: Windows 10/11 environment

---

## Getting Started (PowerShell Commands)

### 1. Backend Setup

```powershell
# Navigate to backend and create virtual environment
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
Copy-Item .env.example .env
# Edit .env with your DATA_GOV_API_KEY and GOOGLE_MAPS_API_KEY

# Run database migrations
alembic upgrade head

# Run tests
python -m pytest -q

# Start backend development server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```powershell
# In a new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Configure environment variables
Copy-Item .env.example .env.local

# Run checks
npm run typecheck
npm run lint
npm run build

# Start frontend development server
npm run dev
```

---

## Verification & Testing
- Backend unit and integration tests: `cd backend; .venv\Scripts\pytest -q`
- Frontend typecheck and build: `cd frontend; npm run typecheck; npm run build`
- Health check verification: `curl http://localhost:8000/api/v1/health`

---

## Project Structure
```
├── backend/
│   ├── alembic/          # Database migrations
│   ├── app/              # FastAPI application core, api, models, services
│   ├── config/           # rates.json, crops.json
│   ├── data/             # Mandi seeds and review records
│   ├── scripts/          # Ingestion, geocoding, and benchmarks
│   └── tests/            # Unit, integration, accuracy, and perf tests
├── frontend/
│   ├── app/              # Next.js App Router pages
│   ├── components/       # Reusable UI components
│   ├── lib/              # API clients, formatting, i18n
│   └── locales/          # English and Hindi dictionary files
└── docs/                 # Context, architecture decisions, API specs, methodology
```
