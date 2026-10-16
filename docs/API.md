# Mandi Arbitrage Advisor - API Reference

The Mandi Arbitrage Advisor API provides real-time net realization calculations, statutory APMC market fee deductions, dynamic logistical freight estimation, and historical price trends for Indian agricultural producers.

- **Base URL**: `http://localhost:8000/api/v1` (Local) / `/api/v1` (Production)
- **Protocol**: HTTP/1.1 and HTTP/2 over TLS
- **Data Exchange**: JSON (`application/json; charset=utf-8`)
- **Interactive Documentation**: `http://localhost:8000/docs` (Swagger UI) / `http://localhost:8000/redoc` (ReDoc)
- **OpenAPI 3.1 Specification**: [docs/openapi.json](file:///C:/Users/VICTUS/Desktop/Projects/mandi-arbitrage/docs/openapi.json)

---

## 1. Quickstart (PowerShell / Bash)

### Health Check
```powershell
curl.exe -s http://127.0.0.1:8000/api/v1/health | jq .
```

### Compare 5 Nearest Mandis for Wheat (Pincode 440001, Nagpur)
```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/v1/compare `
  -H "Content-Type: application/json" `
  -d '{
    "pincode": "440001",
    "commodity": "Wheat",
    "quantity_quintals": 10.0,
    "vehicle": "pickup",
    "quality": { "grade": "Good" },
    "price_basis": "modal",
    "include_other_charges": false,
    "limit": 5
  }' | jq .
```

### 7-Day Historical Price Trend for Mandis 77 and 159
```powershell
curl.exe -s "http://127.0.0.1:8000/api/v1/trend?mandi_ids=77,159&commodity=Wheat&days=7" | jq .
```

---

## 2. Global Architecture & Policies

### Rate Limiting
To protect external routing quotas and prevent service denial, the core comparison engine enforces rate limiting:
- **`POST /api/v1/compare`**: **30 requests per minute per IP address**.
- Exceeded limits trigger an immediate `429 Too Many Requests` response.
- Exemption is permitted for internal health diagnostic sweeps with header `x-bypass-rate-limit: true`.

### Unified Error Envelope
All error responses across the API strictly adhere to the unified standard error schema:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Pincode must be a 6-digit number not starting with 0 (^[1-9][0-9]{5}$)",
    "details": null
  }
}
```

#### Error Code Catalog
| HTTP Code | Error Code | Description |
|---|---|---|
| `422` | `VALIDATION_ERROR` | Request payload fails schema validation or regex checks. |
| `422` | `UNKNOWN_COMMODITY` | Requested crop is not in the supported commodity registry. |
| `422` | `MISSING_LOCATION` | Neither a 6-digit pincode nor a state/district pair was supplied. |
| `422` | `GEOCODE_ERROR` | Failed to resolve geographic coordinates from both Google and Nominatim. |
| `422` | `INVALID_MANDI_IDS` | `mandi_ids` query parameter could not be parsed into integers. |
| `429` | `RATE_LIMIT_EXCEEDED` | Request rate exceeded 30 requests/minute/IP. |
| `401` | `UNAUTHORIZED` | Invalid or missing `X-Admin-Token` header on protected endpoints. |
| `500` | `INTERNAL_SERVER_ERROR` | Unhandled server exception (stack trace suppressed in production). |

### Caching Architecture
The service deploys a two-tier hybrid caching model to guarantee sub-800ms warm p95 response times:

```
[Client Request]
       │
       ▼
[In-Memory TTLCache] ──HIT──► (0.2 ms response)
       │ MISS
       ▼
[SQLite / Postgres Persistent Cache] ──HIT──► (1.5 ms response)
       │ MISS
       ▼
[External API / DB Query] ──► Write to Memory + Persistent DB ──► Return
```

| Cache Layer | TTL | Key Format | Invalidation Policy |
|---|---|---|---|
| **Mandi Prices** | 15 minutes | `(mandi_id, commodity, variety, date)` | Automatic TTL expiry |
| **Metadata Lists** | 1 hour | `meta:states`, `meta:districts:<state>` | Automatic TTL expiry |
| **Geocoding** | Permanent | `pincode:<6-digits>` or `district:<state>:<dist>` | Persistent DB (`geocode_cache`) + 24h memory |
| **Road Distance** | 30 days | `<origin_key>:<mandi_id>` | Persistent DB (`distance_cache`) + 30d memory |

### Data Freshness & Gaps
- **Maximum Price Age**: The engine only considers prices recorded within the past `PRICE_MAX_AGE_DAYS` (default 3 days). Older records are excluded.
- **Stale Price Tagging**: Mandis with price data between 2 and 3 days old are returned with `"is_stale": true` and a `STALE_PRICE` warning.
- **Historical Gaps**: If an APMC mandi was closed or held no auctions on a given calendar day, the 7-day trend series reports `null` for that date. Missing points are **never interpolated or synthesized**.

---

## 3. Endpoints

### 3.1 Comparison Engine

#### `POST /api/v1/compare`
Evaluates and ranks nearby mandis by net financial return after deducting all friction costs.

##### Request Body
```json
{
  "pincode": "440001",
  "state": null,
  "district": null,
  "commodity": "Wheat",
  "variety": null,
  "quantity_quintals": 10.0,
  "vehicle": "pickup",
  "quality": {
    "grade": "Good",
    "custom_pct": null
  },
  "price_basis": "modal",
  "overrides": {
    "market_fee_pct": null,
    "commission_pct": null,
    "rate_per_km": null
  },
  "include_other_charges": false,
  "limit": 5
}
```

##### Response `200 OK`
```json
{
  "query": {
    "pincode": "440001",
    "state": null,
    "district": null,
    "commodity": "Wheat",
    "variety": null,
    "quantity_quintals": "10.0",
    "vehicle": "pickup",
    "quality": {
      "grade": "Good",
      "custom_pct": null
    },
    "price_basis": "modal",
    "overrides": null,
    "include_other_charges": false,
    "limit": 5,
    "resolved_location": {
      "lat": 21.1538,
      "lng": 79.0767,
      "label": "Nagpur, Maharashtra, 440001, India",
      "source": "google"
    }
  },
  "results": [
    {
      "rank": 1,
      "is_nearest": true,
      "mandi": {
        "id": 77,
        "name": "APMC Nagpur",
        "district": "Nagpur",
        "state": "Maharashtra",
        "lat": 21.1498,
        "lng": 79.0821
      },
      "price": {
        "basis": "modal",
        "value": "2926.33",
        "min": "2850.00",
        "max": "3000.00",
        "arrival_date": "2026-10-15",
        "age_days": 1,
        "variety": "Aggregated (3 varieties)",
        "varieties_used": 3,
        "is_stale": false
      },
      "distance": {
        "road_km": 0.92,
        "duration_min": 1.4,
        "source": "routes_api"
      },
      "breakdown": {
        "price_q": "2926.33",
        "quality_cut_q": "0.00",
        "realized_q": "2926.33",
        "mandi_fee_q": "87.79",
        "transport_q": "1.66",
        "other_q": "0.00",
        "net_q": "2836.88",
        "net_total": "28368.84"
      },
      "vs_nearest": {
        "delta_q": "0.00",
        "delta_total": "0.00"
      }
    }
  ],
  "summary": {
    "best_mandi_id": 77,
    "nearest_mandi_id": 77,
    "extra_profit_q": "0.00",
    "extra_profit_total": "0.00"
  },
  "assumptions": {
    "rates_status": "ASSUMPTION_UNVERIFIED",
    "market_fee_pct": "1.00",
    "commission_pct": "2.00",
    "vehicle": "pickup",
    "rate_per_km": "18.00",
    "quality_cut_pct": "0.00",
    "round_trip_factor": "1.00"
  },
  "warnings": [
    {
      "code": "ASSUMED_RATES",
      "message": "Statutory market fees and freight rates are unverified estimates (status: ASSUMPTION_UNVERIFIED)."
    }
  ],
  "meta": {
    "elapsed_ms": 118.45,
    "cache": {
      "geocode": "hit",
      "distance": "hit",
      "prices": "hit"
    },
    "generated_at": "2026-10-17T01:30:00Z"
  }
}
```

##### Comparison Warning Codes
| Warning Code | Explanation |
|---|---|
| `ASSUMED_RATES` | Rates and statutory percentages carry default assumption status (`ASSUMPTION_UNVERIFIED`). |
| `STALE_PRICE` | One or more mandis are reporting market data between 2 and 3 days old. |
| `DISTANCE_FALLBACK` | Real road routing matrix failed or timed out; straight-line haversine * 1.3 approximation used. |
| `GEOCODE_FALLBACK` | Primary Google geocoder failed; OpenStreetMap Nominatim was used as fallback. |
| `FEWER_THAN_LIMIT` | Fewer candidate mandis with active prices exist within the maximum search radius than requested. |
| `NO_PRICE_DATA` | No mandis in radius have reported prices for the commodity within the past 3 days. |

---

### 3.2 Historical Trends

#### `GET /api/v1/trend`
Fetches historical daily prices across candidate mandis for trend comparison.

##### Query Parameters
- `mandi_ids` (string, required): Comma-separated list of mandi IDs, e.g. `77,159`.
- `commodity` (string, required): Canonical crop name, e.g. `Wheat`.
- `days` (integer, optional): Number of historical days, 1 to 30 (default: `7`).

##### Response `200 OK`
```json
{
  "series": [
    {
      "mandi_id": 77,
      "mandi_name": "APMC Nagpur",
      "points": [
        {
          "date": "2026-10-10",
          "modal": "2850.00",
          "min": "2700.00",
          "max": "2900.00",
          "is_seeded": false
        },
        {
          "date": "2026-10-11",
          "modal": null,
          "min": null,
          "max": null,
          "is_seeded": false
        }
      ]
    }
  ]
}
```

---

### 3.3 Metadata Endpoints

- `GET /api/v1/meta/crops`: List supported crops with English/Hindi labels and query aliases.
- `GET /api/v1/meta/vehicles`: Predefined vehicle specifications (capacities in quintals and rates per km).
- `GET /api/v1/meta/rates`: System rate card defaults, state overrides, and quality grade deductions.
- `GET /api/v1/meta/states`: List distinct states with active mandis in database.
- `GET /api/v1/meta/districts?state=Maharashtra`: List distinct districts within a state.

---

### 3.4 Diagnostics & Admin

- `GET /health` and `GET /api/v1/health`: Service liveness check.
- `POST /api/v1/admin/ingest`: Trigger data.gov.in price ingestion. Requires header `X-Admin-Token`.
