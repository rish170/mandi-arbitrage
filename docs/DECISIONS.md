# Architecture & Technical Decisions Log

This document records architectural choices, rationale, and dependency additions per project rules (R8 & R9).

---

## 2026-10-17: Phase 1 Scaffolding

### D-001: Pinned Backend Dependencies (Rule R9 Compliance)
Every backend dependency added to `backend/requirements.txt` has a specific, minimal justification:
- `fastapi==0.115.8`: Core async web framework providing OpenAPI generation, validation, and performance.
- `uvicorn[standard]==0.34.0`: High-performance ASGI server for running FastAPI.
- `pydantic==2.10.6`: Data parsing, strict validation, and schemas for all API payloads and internal models.
- `pydantic-settings==2.7.1`: Robust environment variable loading and validation from `.env`.
- `sqlalchemy==2.0.38`: Modern SQLAlchemy 2 async ORM for database modeling and query execution.
- `alembic==1.14.1`: Database migrations engine for SQLite and PostgreSQL schema evolution.
- `aiosqlite==0.21.0`: Async SQLite driver for fast local development and testing without external database setup.
- `asyncpg==0.30.0`: Async PostgreSQL driver for production deployments on Railway.
- `httpx==0.28.1`: Modern async HTTP client for external API requests (data.gov.in, Google Maps, Nominatim).
- `cachetools==5.5.2`: In-memory TTL caching for geocoding and distance calculations.
- `slowapi==0.1.9`: In-memory IP-based rate limiting (30 req/min on `/compare`) to prevent quota exhaustion.
- `pytest==8.3.4`: Testing framework for backend unit, integration, and accuracy tests.
- `pytest-asyncio==0.25.3`: Pytest extension for executing async test coroutines natively.
- `respx==0.22.0`: Mocking utility for HTTPX requests in unit and integration testing.

### D-002: Dual Database Strategy (SQLite for local, Postgres for production)
- **Decision**: Local development runs on SQLite via `aiosqlite`; production runs on PostgreSQL via `asyncpg`.
- **Rationale**: Keeps local onboarding zero-config (no Postgres or Docker needed on Windows) while maintaining standard SQL and Alembic migration compatibility for cloud deployment on Railway.

### D-003: Batch Migrations for SQLite in Alembic
- **Decision**: Enabled `render_as_batch=True` in `alembic/env.py`.
- **Rationale**: SQLite does not support standard `ALTER TABLE` operations (e.g. dropping columns, modifying constraints). Batch mode creates a temporary table, copies data, and swaps tables transparently.

### D-004: Mandi Registry Geocoding Fallback Chain
- **Decision**: In Phase 2, the offline mandi registry build script will first attempt Google Geocoding (`"<market> APMC, <district>, <state>, India"`). If Google Geocoding returns no result, times out, or encounters quota limits, the script automatically falls back to OpenStreetMap Nominatim with 1 req/s rate limiting.
- **Rationale**: Maximizes mandi geocoding coverage while saving Google quota and handling edge-case mandi names cleanly. Any low-confidence coordinates will be written to `data/mandis_review.csv`.

### D-005: Money Arithmetic with Python Decimal (Rule R4)
- **Decision**: All financial and quantity mathematics strictly utilize Python `Decimal`. Floating-point arithmetic is forbidden in calculations.
- **Rationale**: Guarantees zero precision loss in currency and quintal divisions, rounding strictly at the presentation boundary to 2 decimal places.

---

## 2026-10-17: Phase 2 Data Layer Verification

### D-006: data.gov.in Mandi Price Resource Verification & Historical Probe
- **Live Verification**:
  - Resource ID tested: `9ef84268-d588-465a-a308-a864a43d0070` ("Current Daily Price of Various Commodities from Various Markets (Mandi)").
  - Total records currently active for Maharashtra: 1,096 records across diverse commodities and APMC markets.
  - Active field schema: `state`, `district`, `market`, `commodity`, `variety`, `grade`, `arrival_date`, `min_price`, `max_price`, `modal_price`.
  - Date format returned: `dd/mm/yyyy` (e.g., `16/10/2026`).
- **History Probe Findings**:
  - We probed `filters[arrival_date]` for prior dates (`15/10/2026`, `14/10/2026`, `10/10/2026`, etc.).
  - Result: The API returns the exact same count and records for the current day (`16/10/2026`). The upstream CKAN resource operates as a point-in-time daily snapshot, overwriting or retaining only current daily arrivals.
  - Conclusion: Historical backfill via the API is **not supported** by this data.gov.in resource. Daily history must accumulate via our twice-daily automated ingestion job storing persistent daily snapshots in our local database.
  - For historical trend charts prior to local accumulation, `scripts/seed_demo_history.py` will generate flagged demo series (`is_seeded=true`, source `demo_seed`) using bounded random walk, ensuring transparent labeling.

---

## 2026-10-17: Phase 3-7 Engine, UI, and Deployment

### D-007: Single Batched Routing Call with Haversine Fallback
- **Decision**: Candidate mandis are pre-ranked by Haversine distance, and the top 10 candidates are queried in a single batched `computeRouteMatrix` call to the Google Routes API. If Google Routes returns HTTP 403/429/500 or times out (1.2 s), the engine gracefully falls back to `Haversine * 1.3` road factor with `DISTANCE_FALLBACK` warning.
- **Rationale**: Eliminates $N$ individual network round trips, meeting the sub-800ms warm latency SLA while remaining fully functional even when external Google API quotas or network partitions occur.

### D-008: Multi-Tier Persistent and In-Memory Caching
- **Decision**: Origin pincodes, coordinates, and road distances are stored permanently in SQLite/PostgreSQL `geocode_cache` and `distance_cache` tables, fronted by an in-memory `cachetools.TTLCache`.
- **Rationale**: Reduces repeat query latency from ~1.5s down to <100ms and eliminates redundant Google API billable requests.

### D-009: Liquid Glass Design System with Zero-Forbidden Hues (Rule R1)
- **Decision**: Enforced earthy farm palette tokens (Forest, Wheat, Clay, Soil) with translucent glass backdrop filters (`blur(24px) saturate(180%)`) and zero colors between 190° and 340° hue angles.
- **Rationale**: Prevents generic "AI SaaS" aesthetic (no blue/purple gradients) and delivers a high-contrast, tactile, farmer-first utility. Verified via automated WCAG contrast and palette AST scanning scripts.

### D-010: Complete Bilingual String Translation and Zero Untranslated Keys
- **Decision**: Maintained 100% key parity between `frontend/locales/en.json` and `frontend/locales/hi.json`, verified by automated Vitest parity tests.
- **Rationale**: Farmers in Maharashtra and rural India require natural, native Devanagari terminology for agricultural commodities, market charges, and quality grades.

### D-011: PostgreSQL Connection URL Auto-Normalization
- **Decision**: Implemented automatic string transformation in `app.db.resolve_db_url()` to convert incoming `postgres://` or `postgresql://` strings to `postgresql+asyncpg://`.
- **Rationale**: Cloud PaaS providers like Railway provision database connection strings using legacy `postgres://` schemas. Converting them seamlessly in the driver initialization enables zero-configuration deployment.

