import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { CostBreakdown } from "@/components/CostBreakdown";
import { I18nProvider } from "@/lib/i18n";
import { CompareResultItem } from "@/lib/api";

const mockResults: CompareResultItem[] = [
  {
    rank: 1,
    is_nearest: false,
    mandi: { id: 1, name: "APMC Nagpur", district: "Nagpur", state: "Maharashtra", lat: 21.1, lng: 79.1 },
    price: { basis: "modal", value: "3000.00", arrival_date: "2026-10-15", age_days: 1, variety: "Lokwan", varieties_used: 1, is_stale: false },
    distance: { road_km: 10.0, duration_min: 20.0, source: "routes_api" },
    breakdown: { price_q: "3000.00", quality_cut_q: "0.00", realized_q: "3000.00", mandi_fee_q: "90.00", transport_q: "18.00", other_q: "0.00", net_q: "2892.00", net_total: "28920.00" },
    vs_nearest: { delta_q: "100.00", delta_total: "1000.00" },
  },
];

describe("CostBreakdown Component", () => {
  it("renders stacked progress bars and accessible text alternatives", () => {
    render(
      <I18nProvider>
        <CostBreakdown results={mockResults} />
      </I18nProvider>
    );

    expect(screen.getByText(/Cost Breakdown/i)).toBeDefined();
    expect(screen.getAllByText(/APMC Nagpur/i).length).toBeGreaterThan(0);

    const progressbar = screen.getByRole("progressbar");
    expect(progressbar).toBeDefined();
    expect(progressbar.getAttribute("aria-label")).toContain("APMC Nagpur");
  });
});
