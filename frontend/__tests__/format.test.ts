import { describe, it, expect } from "vitest";
import { formatCurrency, formatNumber, formatDistance } from "@/lib/format";

describe("Formatting Helpers (en-IN Standards)", () => {
  describe("formatCurrency", () => {
    it("formats Indian rupees with en-IN digit grouping (lakhs and crores)", () => {
      // 1,000 -> ₹1,000.00
      expect(formatCurrency(1000)).toBe("₹1,000.00");
      // 1,23,456.78 -> ₹12,34,567.89
      expect(formatCurrency(1234567.89)).toBe("₹12,34,567.89");
    });

    it("handles string numeric inputs from Decimal representations", () => {
      expect(formatCurrency("2900.50")).toBe("₹2,900.50");
      expect(formatCurrency("7800")).toBe("₹7,800.00");
    });

    it("handles zero correctly", () => {
      expect(formatCurrency(0)).toBe("₹0.00");
      expect(formatCurrency("0")).toBe("₹0.00");
    });

    it("handles null, undefined, and invalid inputs with fallback dash", () => {
      expect(formatCurrency(null)).toBe("—");
      expect(formatCurrency(undefined)).toBe("—");
      expect(formatCurrency("invalid")).toBe("—");
    });

    it("supports hiding decimals via option", () => {
      expect(formatCurrency(1234567, { showDecimals: false })).toBe("₹12,34,567");
    });

    it("supports custom symbol", () => {
      expect(formatCurrency(2500, { symbol: "Rs. " })).toBe("Rs. 2,500.00");
    });
  });

  describe("formatNumber", () => {
    it("formats integer with Indian grouping", () => {
      expect(formatNumber(1000000)).toBe("10,00,000");
      expect(formatNumber(50)).toBe("50");
    });

    it("handles specified decimal precision", () => {
      expect(formatNumber(1234.5678, 2)).toBe("1,234.57");
    });
  });

  describe("formatDistance", () => {
    it("formats road kilometers with 1 decimal place", () => {
      expect(formatDistance(25.43)).toBe("25.4 km");
      expect(formatDistance("80")).toBe("80.0 km");
    });

    it("handles empty values with dash", () => {
      expect(formatDistance(null)).toBe("—");
      expect(formatDistance("")).toBe("—");
    });
  });
});
