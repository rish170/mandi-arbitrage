# API Latency Performance & Benchmark Report

Empirical latency benchmark results for `POST /api/v1/compare` across $N=60$ requests executed at concurrency level 5.

## Benchmark Summary

| Metric | Cold Cache Target | Cold Result | Warm Cache Target | Warm Result | Target Met |
|---|---|---|---|---|---|
| **Median (p50)** | - | `228.6 ms` | - | `216.0 ms` | YES |
| **p95** | < 3000 ms | `1184.2 ms` | < 800 ms | `360.5 ms` | YES |
| **p99** | < 3000 ms | `1214.5 ms` | < 1000 ms | `422.8 ms` | YES |
| **Max Latency** | < 3000 ms | `1246.3 ms` | < 1500 ms | `463.2 ms` | YES |
| **Failed / Errors** | 0 | `0` | 0 | `0` | YES |

## Environment Notes

- **Operating System**: Windows
- **Python Runtime**: Python 3.12 (venv)
- **Database**: SQLite (WAL mode, aiosqlite async engine)
- **HTTP Client**: `httpx` async client with 5 concurrent workers
- **Distance Service**: Batched Routes Matrix API with automatic haversine * 1.3 fallback (Google Routes API enabled or gracefully falling back)

## Architectural Optimizations

The Mandi Arbitrage Advisor achieves low response latency via 5 deliberate architectural decisions:
1. **Single Batched Routing Call**: Rather than sending $N$ separate point-to-point HTTP requests for each mandi, the engine executes a single batched `computeRouteMatrix` call covering all candidate mandis simultaneously.
2. **Zero Live Price Scraping**: The request execution path never queries external government portals live. All market prices are queried from pre-indexed local SQLite/PostgreSQL snapshot tables with composite indexes on `(mandi_id, commodity, arrival_date)`.
3. **Multi-Tier In-Memory TTL Caching**: Layered in-memory caching eliminates redundant computation:
   - Latest mandi prices cached for 15 minutes (`TTLCache(ttl=900)`).
   - State & district metadata cached for 1 hour (`TTLCache(ttl=3600)`).
   - Road distances cached in memory and database for 30 days.
   - Pincode and district geocoding cached permanently in SQLite `GeocodeCache`.
4. **Concurrent I/O Gathering**: Independent operations—batched distance calculation and database price retrieval—are executed concurrently using `asyncio.gather` on dedicated asynchronous sessions.
5. **Strict External Timeouts & Fast Fallbacks**: External Google API calls enforce strict timeouts (1.0s geocode, 1.2s distance). Any transient network delay or quota issue immediately triggers an instant haversine * 1.3 approximation, preventing API degradation.