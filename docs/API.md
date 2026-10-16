# Mandi Arbitrage Advisor - REST API Documentation

Base URL: `/api/v1`

---

## Overview
All endpoints accept and return JSON. Error responses follow the unified schema:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable description",
    "details": null
  }
}
```

---

## 1. System & Health

### `GET /health` and `GET /api/v1/health`
Checks API operational status and returns current service timestamp.

#### Response: `200 OK`
```json
{
  "status": "ok",
  "version": "0.01.00",
  "timestamp": "2026-10-17T00:00:00Z"
}
```

---

## 2. Metadata Endpoints

### `GET /api/v1/meta/crops`
Returns supported agricultural commodities, English/Hindi names, and data.gov.in aliases.

### `GET /api/v1/meta/vehicles`
Returns predefined freight vehicle types, capacities in quintals, and standard rates per km.

### `GET /api/v1/meta/rates`
Returns statutory APMC market fee percentages, default commissions, quality grade cuts, and assumption status (`ASSUMPTION_UNVERIFIED`).

### `GET /api/v1/meta/states`
Returns list of states available in the mandi registry.

### `GET /api/v1/meta/districts?state=Maharashtra`
Returns list of districts for a selected state.

---

## 3. Comparison Engine

### `POST /api/v1/compare`
Calculates net realization across the 5 nearest mandis for a given crop, quantity, vehicle, quality cut, and location.

#### Request Parameters
- `pincode`: 6-digit Indian postal code (`^[1-9][0-9]{5}$`) OR `state` + `district`
- `commodity`: Crop name (e.g., "Wheat", "Soyabean")
- `variety`: (Optional) Variety filter
- `quantity_quintals`: Total produce quantity (default: 10)
- `vehicle`: Vehicle ID (`tempo`, `pickup`, `mini_truck`, `truck`)
- `quality`: `{ "grade": "Good" }` or `{ "custom_pct": 5.0 }`
- `price_basis`: `"modal"`, `"min"`, or `"max"`
- `overrides`: (Optional) Custom fees or per-km transport rates
- `include_other_charges`: Boolean
- `limit`: Number of results (default 5, max 10)

#### Warning Codes
- `STALE_PRICE`: Price snapshot is between 2 and 3 days old.
- `DISTANCE_FALLBACK`: Road distance service unavailable; haversine * 1.3 utilized.
- `GEOCODE_FALLBACK`: Google geocoder unavailable; Nominatim utilized.
- `FEWER_THAN_LIMIT`: Fewer than requested candidate mandis found within search radius.
- `NO_PRICE_DATA`: Mandi excluded due to lack of recent price data.
- `ASSUMED_RATES`: Default rates used with unverified status.

---

## 4. Price History & Trends

### `GET /api/v1/trend?mandi_ids=1,2,3&commodity=Wheat&days=7`
Returns 7-day daily modal, min, and max price points for selected mandis. Missing days are represented as `null` points.

---

## 5. Administration

### `POST /api/v1/admin/ingest`
Triggers an asynchronous price ingestion job from data.gov.in. Protected by `X-Admin-Token` header.
