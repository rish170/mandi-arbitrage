import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { SearchPanel } from "@/components/SearchPanel";
import { I18nProvider } from "@/lib/i18n";
import * as apiModule from "@/lib/api";

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof apiModule>();
  return {
    ...actual,
    api: {
      getDistricts: vi.fn().mockResolvedValue({ state: "Maharashtra", districts: ["Nagpur", "Wardha", "Akola"] }),
      getVehicles: vi.fn().mockResolvedValue({
        vehicles: {
          tempo: { capacity_q: 8, rate_per_km: 14, description: "Tempo" },
          pickup: { capacity_q: 15, rate_per_km: 18, description: "Pickup" },
        },
      }),
      compareMandis: vi.fn(),
    },
  };
});

describe("SearchPanel Component", () => {
  const onSearchMock = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  const renderPanel = async (isLoading = false) => {
    const result = render(
      <I18nProvider>
        <SearchPanel onSearch={onSearchMock} isLoading={isLoading} />
      </I18nProvider>
    );
    await waitFor(() => {
      expect(
        screen.getByRole("button", {
          name: isLoading ? /comparing mandis/i : /calculate net profit/i,
        })
      ).toBeDefined();
    });
    return result;
  };

  it("validates 6-digit pincode and rejects invalid input", async () => {
    await renderPanel();

    const pincodeInput = screen.getByLabelText(/6-digit pincode/i);
    fireEvent.change(pincodeInput, { target: { value: "123" } });

    const submitBtn = screen.getByRole("button", { name: /calculate net profit/i });
    fireEvent.click(submitBtn);

    expect(onSearchMock).not.toHaveBeenCalled();
    expect(await screen.findByText(/please enter a valid 6-digit/i)).toBeDefined();
  });

  it("switches to State + District mode and validates district selection", async () => {
    await renderPanel();

    const districtModeBtn = screen.getByRole("button", { name: /state \+ district/i });
    fireEvent.click(districtModeBtn);

    const districtSelect = await screen.findByLabelText(/district/i);
    fireEvent.change(districtSelect, { target: { value: "" } });

    const submitBtn = screen.getByRole("button", { name: /calculate net profit/i });
    fireEvent.click(submitBtn);

    expect(onSearchMock).not.toHaveBeenCalled();
    expect(await screen.findByText(/please select a district/i)).toBeDefined();
  });

  it("updates quantity via quick chips", async () => {
    await renderPanel();

    const chip25 = screen.getByRole("button", { name: "25q" });
    fireEvent.click(chip25);

    const qtyInput = screen.getByLabelText(/quantity/i) as HTMLInputElement;
    expect(qtyInput.value).toBe("25");
  });

  it("builds correct request payload and calls onSearch", async () => {
    await renderPanel();

    const pincodeInput = screen.getByLabelText(/6-digit pincode/i);
    fireEvent.change(pincodeInput, { target: { value: "440001" } });

    const cropSelect = screen.getByLabelText(/crop/i);
    fireEvent.change(cropSelect, { target: { value: "Wheat" } });

    const chip10 = screen.getByRole("button", { name: "10q" });
    fireEvent.click(chip10);

    const submitBtn = screen.getByRole("button", { name: /calculate net profit/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(onSearchMock).toHaveBeenCalledTimes(1);
    });

    const callArg = onSearchMock.mock.calls[0][0];
    expect(callArg.pincode).toBe("440001");
    expect(callArg.commodity).toBe("Wheat");
    expect(callArg.quantity_quintals).toBe(10);
    expect(callArg.vehicle).toBe("pickup");
    expect(callArg.quality.grade).toBe("Good");
  });

  it("disables submit button and shows loading text when isLoading is true", async () => {
    await renderPanel(true);

    const submitBtn = screen.getByRole("button", { name: /comparing mandis/i });
    expect(submitBtn).toBeDefined();
    expect(submitBtn.hasAttribute("disabled")).toBe(true);
  });
});
