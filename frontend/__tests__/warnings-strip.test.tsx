import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { WarningsStrip } from "@/components/WarningsStrip";
import { I18nProvider } from "@/lib/i18n";
import { WarningItem } from "@/lib/api";

describe("WarningsStrip Component", () => {
  it("renders translated messages for all backend warning codes", () => {
    const warnings: WarningItem[] = [
      { code: "STALE_PRICE", message: "Price is stale" },
      { code: "DISTANCE_FALLBACK", message: "Distance fallback used" },
      { code: "GEOCODE_FALLBACK", message: "Geocode fallback used" },
      { code: "FEWER_THAN_LIMIT", message: "Fewer than limit" },
      { code: "NO_PRICE_DATA", message: "No price data" },
      { code: "ASSUMED_RATES", message: "Assumed rates used" },
    ];

    render(
      <I18nProvider>
        <WarningsStrip warnings={warnings} />
      </I18nProvider>
    );

    expect(screen.getByText(/\[STALE_PRICE\]:/i)).toBeDefined();
    expect(screen.getByText(/\[DISTANCE_FALLBACK\]:/i)).toBeDefined();
    expect(screen.getByText(/\[GEOCODE_FALLBACK\]:/i)).toBeDefined();
    expect(screen.getByText(/\[FEWER_THAN_LIMIT\]:/i)).toBeDefined();
    expect(screen.getByText(/\[NO_PRICE_DATA\]:/i)).toBeDefined();
    expect(screen.getByText(/\[ASSUMED_RATES\]:/i)).toBeDefined();
  });

  it("renders null when warnings list is empty", () => {
    const { container } = render(
      <I18nProvider>
        <WarningsStrip warnings={[]} />
      </I18nProvider>
    );

    expect(container.firstChild).toBeNull();
  });
});
