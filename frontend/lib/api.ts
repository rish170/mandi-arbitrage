/**
 * Typed API Client for Mandi Arbitrage Advisor
 * Mirrored from docs/openapi.json and API contract
 */

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
}

export interface CropItem {
  id: string;
  name_en: string;
  name_hi: string;
  aliases: string[];
}

export interface CropsResponse {
  crops: CropItem[];
}

export interface VehicleSpec {
  capacity_q: number;
  rate_per_km: number;
  description: string;
}

export interface VehiclesResponse {
  vehicles: Record<string, VehicleSpec>;
}

export interface RatesResponse {
  status: string;
  note: string;
  market_fee_pct_default: string;
  commission_pct_default: string;
  state_overrides: Record<string, { market_fee_pct?: number; commission_pct?: number }>;
  vehicles: Record<string, { capacity_q: number; rate_per_km: number; description: string }>;
  quality_grades: Record<string, string>;
  custom_quality_cut_pct_range: Record<string, string>;
  other_charges_per_quintal: Record<string, string>;
  fallback_distance: Record<string, string>;
  defaults: Record<string, unknown>;
}

export interface StatesResponse {
  states: string[];
}

export interface DistrictsResponse {
  state: string;
  districts: string[];
}

export interface QualityInput {
  grade?: string | null;
  custom_pct?: number | string | null;
}

export interface OverridesInput {
  market_fee_pct?: number | string | null;
  commission_pct?: number | string | null;
  rate_per_km?: number | string | null;
}

export interface CompareRequest {
  pincode?: string | null;
  state?: string | null;
  district?: string | null;
  commodity: string;
  variety?: string | null;
  quantity_quintals?: number | string;
  vehicle?: string;
  quality?: QualityInput;
  price_basis?: "modal" | "min" | "max";
  overrides?: OverridesInput | null;
  include_other_charges?: boolean;
  limit?: number;
}

export interface MandiBrief {
  id: number;
  name: string;
  district: string;
  state: string;
  lat: number;
  lng: number;
}

export interface PriceBrief {
  basis: string;
  value: string;
  min?: string | null;
  max?: string | null;
  arrival_date: string;
  age_days: number;
  variety: string;
  varieties_used: number;
  is_stale: boolean;
}

export interface DistanceBrief {
  road_km: number;
  duration_min: number;
  source: string;
}

export interface BreakdownBrief {
  price_q: string;
  quality_cut_q: string;
  realized_q: string;
  mandi_fee_q: string;
  transport_q: string;
  other_q: string;
  net_q: string;
  net_total: string;
}

export interface VsNearestBrief {
  delta_q: string;
  delta_total: string;
}

export interface CompareResultItem {
  rank: number;
  is_nearest: boolean;
  mandi: MandiBrief;
  price: PriceBrief;
  distance: DistanceBrief;
  breakdown: BreakdownBrief;
  vs_nearest: VsNearestBrief;
}

export interface SummaryBrief {
  best_mandi_id: number;
  nearest_mandi_id: number;
  extra_profit_q: string;
  extra_profit_total: string;
}

export interface AssumptionsBrief {
  rates_status: string;
  market_fee_pct: string;
  commission_pct: string;
  vehicle: string;
  rate_per_km: string;
  quality_cut_pct: string;
  round_trip_factor: string;
}

export interface WarningItem {
  code: string;
  message: string;
}

export interface CompareMeta {
  elapsed_ms: number;
  cache: {
    geocode: string;
    distance: string;
    prices: string;
  };
  generated_at?: string;
}

export interface CompareResponse {
  query: Record<string, unknown>;
  results: CompareResultItem[];
  summary: SummaryBrief;
  assumptions: AssumptionsBrief;
  warnings: WarningItem[];
  meta: CompareMeta;
}

export interface TrendPoint {
  date: string;
  modal?: string | null;
  min?: string | null;
  max?: string | null;
  is_seeded: boolean;
}

export interface MandiTrendSeries {
  mandi_id: number;
  mandi_name: string;
  district?: string;
  points: TrendPoint[];
}

export interface PriceTrendResponse {
  commodity: string;
  days: number;
  series: MandiTrendSeries[];
}

export class ApiError extends Error {
  public code: string;
  public status: number;
  public details?: unknown;

  constructor(message: string, code = "UNKNOWN_ERROR", status = 500, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

const DEFAULT_TIMEOUT_MS = 8000;

interface ApiErrorPayload {
  error?: { code?: string; message?: string; details?: unknown };
  detail?: Array<{ msg?: string }>;
}

async function requestWithTimeout<T>(
  endpoint: string,
  options: RequestInit = {},
  retried = false
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);

  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...(options.headers || {}),
      },
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      let errorBody: ApiErrorPayload | null = null;
      try {
        errorBody = (await res.json()) as ApiErrorPayload;
      } catch {
        // non-JSON error response
      }

      if (res.status === 429) {
        throw new ApiError(
          "Rate limit exceeded (30 req/min). Please wait a moment before trying again.",
          "RATE_LIMIT_EXCEEDED",
          429
        );
      }

      if (res.status === 422) {
        const msg =
          errorBody?.error?.message ||
          errorBody?.detail?.[0]?.msg ||
          "Validation failed. Please verify your inputs.";
        throw new ApiError(msg, "VALIDATION_ERROR", 422, errorBody?.detail);
      }

      const code = errorBody?.error?.code || "API_ERROR";
      const message = errorBody?.error?.message || `Server returned status ${res.status}`;
      throw new ApiError(message, code, res.status, errorBody?.error?.details);
    }

    return (await res.json()) as T;
  } catch (err: unknown) {
    clearTimeout(timeoutId);

    if (err instanceof ApiError) {
      throw err;
    }

    const isAbort = (err as Error)?.name === "AbortError";
    const errorMsg = isAbort
      ? "Request timed out after 8 seconds. The server may be waking up."
      : (err as Error)?.message || "Network error occurred";

    // Retry once on network error or timeout
    if (!retried) {
      return requestWithTimeout<T>(endpoint, options, true);
    }

    throw new ApiError(
      errorMsg,
      isAbort ? "TIMEOUT" : "NETWORK_ERROR",
      isAbort ? 408 : 0,
      err
    );
  }
}

export const api = {
  getHealth: () => requestWithTimeout<HealthResponse>("/health"),

  getCrops: () => requestWithTimeout<CropsResponse>("/api/v1/meta/crops"),

  getVehicles: () => requestWithTimeout<VehiclesResponse>("/api/v1/meta/vehicles"),

  getRates: () => requestWithTimeout<RatesResponse>("/api/v1/meta/rates"),

  getStates: () => requestWithTimeout<StatesResponse>("/api/v1/meta/states"),

  getDistricts: (state: string) =>
    requestWithTimeout<DistrictsResponse>(
      `/api/v1/meta/districts?state=${encodeURIComponent(state)}`
    ),

  compareMandis: (req: CompareRequest) =>
    requestWithTimeout<CompareResponse>("/api/v1/compare", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  getTrend: (mandiIds: number[], commodity: string, days = 7) => {
    const ids = mandiIds.join(",");
    return requestWithTimeout<PriceTrendResponse>(
      `/api/v1/trend?mandi_ids=${encodeURIComponent(ids)}&commodity=${encodeURIComponent(
        commodity
      )}&days=${days}`
    );
  },
};
