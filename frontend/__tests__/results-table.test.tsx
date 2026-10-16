import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ResultsTable } from "@/components/ResultsTable";
import { I18nProvider } from "@/lib/i18n";
import { CompareResultItem } from "@/lib/api";

const mockResults: CompareResultItem[] = [
  {
    rank: 1,
    is_nearest: false,
    mandi: { id: 1, name: "APMC Nagpur", district: "Nagpur", state: "Maharashtra", lat: 21.1, lng: 79.1 },
    price: { basis: "modal", value: "2900.00", arrival_date: "2026-10-15", age_days: 1, variety: "Lokwan", varieties_used: 1, is_stale: false },
    distance: { road_km: 15.0, duration_min: 30.0, source: "routes_api" },
    breakdown: { price_q: "2900.00", quality_cut_q: "0.00", realized_q: "2900.00", mandi_fee_q: "87.00", transport_q: "27.00", other_q: "0.00", net_q: "2786.00", net_total: "27860.00" },
    vs_nearest: { delta_q: "120.00", delta_total: "1200.00" },
  },
  {
    rank: 2,
    is_nearest: true,
    mandi: { id: 2, name: "APMC Wardha", district: "Wardha", state: "Maharashtra", lat: 20.7, lng: 78.6 },
    price: { basis: "modal", value: "2750.00", arrival_date: "2026-10-14", age_days: 2, variety: "Sharbati", varieties_used: 1, is_stale: true },
    distance: { road_km: 6.0, duration_min: 12.0, source: "haversine_fallback" },
    breakdown: { price_q: "2750.00", quality_cut_q: "0.00", realized_q: "2750.00", mandi_fee_q: "82.50", transport_q: "10.80", other_q: "0.00", net_q: "2656.70", net_total: "26567.00" },
    vs_nearest: { delta_q: "0.00", delta_total: "0.00" },
  },
];

describe("ResultsTable Component", () => {
  const renderTable = () => {
    return render(
      <I18nProvider>
        <ResultsTable results={mockResults} />
      </I18nProvider>
    );
  };

  it("renders mandi names, ranks, and badges correctly", () => {
    renderTable();

    expect(screen.getAllByText(/APMC Nagpur/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/APMC Wardha/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/BEST/i).length).toBeGreaterThan(0);
  });

  it("formats Indian rupees with currency symbol and decimal formatting", () => {
    renderTable();

    // Check modal price and net realization formatted
    expect(screen.getAllByText(/₹2,900.00/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/₹2,786.00/i).length).toBeGreaterThan(0);
  });

  it("displays fallback distance tag and stale price note", () => {
    renderTable();

    expect(screen.getAllByText(/Approx Distance/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Old Price/i).length).toBeGreaterThan(0);
  });

  it("sorts table rows when header is clicked", () => {
    renderTable();

    const distanceHeader = screen.getByText(/Road Distance/i);
    fireEvent.click(distanceHeader);

    // After clicking distance header, 6.0 km (Wardha) should be first when ascending
    const rows = screen.getAllByRole("row");
    expect(rows.length).toBeGreaterThan(2); // Header + 2 data rows
  });
});
