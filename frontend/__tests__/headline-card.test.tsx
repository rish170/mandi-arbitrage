import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { HeadlineCard } from "@/components/HeadlineCard";
import { I18nProvider } from "@/lib/i18n";
import { CompareResponse } from "@/lib/api";

const mockResponseDifferent: CompareResponse = {
  query: { commodity: "Wheat", quantity_quintals: 10 },
  results: [
    {
      rank: 1,
      is_nearest: false,
      mandi: { id: 1, name: "APMC Nagpur", district: "Nagpur", state: "Maharashtra", lat: 21.1, lng: 79.1 },
      price: { basis: "modal", value: "2900.00", arrival_date: "2026-10-15", age_days: 1, variety: "Lokwan", varieties_used: 1, is_stale: false },
      distance: { road_km: 12.0, duration_min: 25.0, source: "routes_api" },
      breakdown: { price_q: "2900.00", quality_cut_q: "0.00", realized_q: "2900.00", mandi_fee_q: "87.00", transport_q: "21.60", other_q: "0.00", net_q: "2791.40", net_total: "27914.00" },
      vs_nearest: { delta_q: "150.00", delta_total: "1500.00" },
    },
    {
      rank: 2,
      is_nearest: true,
      mandi: { id: 2, name: "APMC Wardha", district: "Wardha", state: "Maharashtra", lat: 20.7, lng: 78.6 },
      price: { basis: "modal", value: "2750.00", arrival_date: "2026-10-15", age_days: 1, variety: "Lokwan", varieties_used: 1, is_stale: false },
      distance: { road_km: 5.0, duration_min: 10.0, source: "routes_api" },
      breakdown: { price_q: "2750.00", quality_cut_q: "0.00", realized_q: "2750.00", mandi_fee_q: "82.50", transport_q: "9.00", other_q: "0.00", net_q: "2641.40", net_total: "26414.00" },
      vs_nearest: { delta_q: "0.00", delta_total: "0.00" },
    },
  ],
  summary: {
    best_mandi_id: 1,
    nearest_mandi_id: 2,
    extra_profit_q: "150.00",
    extra_profit_total: "1500.00",
  },
  assumptions: {
    rates_status: "ASSUMPTION_UNVERIFIED",
    market_fee_pct: "1.0",
    commission_pct: "2.0",
    vehicle: "pickup",
    rate_per_km: "18.0",
    quality_cut_pct: "0.0",
    round_trip_factor: "1.0",
  },
  warnings: [],
  meta: { elapsed_ms: 120, cache: { geocode: "hit", distance: "hit", prices: "hit" } },
};

const mockResponseSame: CompareResponse = {
  ...mockResponseDifferent,
  results: [
    {
      ...mockResponseDifferent.results[0],
      rank: 1,
      is_nearest: true,
    },
  ],
  summary: {
    best_mandi_id: 1,
    nearest_mandi_id: 1,
    extra_profit_q: "0.00",
    extra_profit_total: "0.00",
  },
};

describe("HeadlineCard Component", () => {
  it("renders comparison sentence when best mandi != nearest mandi", () => {
    render(
      <I18nProvider>
        <HeadlineCard data={mockResponseDifferent} />
      </I18nProvider>
    );

    expect(screen.getByText(/APMC Nagpur/i)).toBeDefined();
    expect(screen.getByText(/APMC Wardha/i)).toBeDefined();
    expect(screen.getByText(/Selling at/i)).toBeDefined();
    expect(screen.getByText(/₹150.00/i)).toBeDefined();
  });

  it("renders plain statement when best mandi == nearest mandi", () => {
    render(
      <I18nProvider>
        <HeadlineCard data={mockResponseSame} />
      </I18nProvider>
    );

    expect(screen.getByText(/is both your nearest mandi/i)).toBeDefined();
    expect(screen.getByText(/₹2,791.40/i)).toBeDefined();
  });
});
