"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { ChevronDown, ChevronUp, Loader2, Info } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { api, CompareRequest, VehicleSpec } from "@/lib/api";

const MAHARASHTRA_DISTRICTS_FALLBACK = [
  "Ahmednagar",
  "Akola",
  "Amravati",
  "Aurangabad",
  "Beed",
  "Bhandara",
  "Buldhana",
  "Chandrapur",
  "Dhule",
  "Gadchiroli",
  "Gondia",
  "Hingoli",
  "Jalgaon",
  "Jalna",
  "Kolhapur",
  "Latur",
  "Nagpur",
  "Nanded",
  "Nandurbar",
  "Nashik",
  "Osmanabad",
  "Parbhani",
  "Pune",
  "Raigad",
  "Ratnagiri",
  "Sangli",
  "Satara",
  "Sindhudurg",
  "Solapur",
  "Thane",
  "Wardha",
  "Washim",
  "Yavatmal",
];

const CROPS = [
  { id: "Wheat", key: "wheat", defaultRate: 2900 },
  { id: "Soyabean", key: "soyabean", defaultRate: 6800 },
  { id: "Cotton", key: "cotton", defaultRate: 7200 },
  { id: "Onion", key: "onion", defaultRate: 2400 },
  { id: "Tomato", key: "tomato", defaultRate: 1500 },
  { id: "Potato", key: "potato", defaultRate: 1800 },
  { id: "Rice", key: "rice", defaultRate: 3100 },
];

const DEFAULT_VEHICLES: Record<string, VehicleSpec> = {
  tempo: { capacity_q: 8, rate_per_km: 14, description: "Small 3-wheeler/Tata Ace" },
  pickup: { capacity_q: 15, rate_per_km: 18, description: "Bolero Pickup" },
  mini_truck: { capacity_q: 40, rate_per_km: 26, description: "Eicher 14ft / 17ft" },
  truck: { capacity_q: 100, rate_per_km: 38, description: "10-wheeler / 12-wheeler" },
};

const STORAGE_KEY = "mandi_last_search";

export interface SearchPanelProps {
  onSearch: (request: CompareRequest) => void;
  isLoading?: boolean;
}

function getInitialSearchState() {
  if (typeof window === "undefined") return null;
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : null;
  } catch {
    return null;
  }
}

export function SearchPanel({ onSearch, isLoading = false }: SearchPanelProps) {
  const { t, lang } = useI18n();

  const [initialSaved] = useState(() => getInitialSearchState());

  // Mode: "pincode" | "district"
  const [mode, setMode] = useState<"pincode" | "district">(
    initialSaved?.mode === "district" ? "district" : "pincode"
  );
  const [pincode, setPincode] = useState<string>(initialSaved?.pincode || "440001");
  const [state, setState] = useState<string>(initialSaved?.state || "Maharashtra");
  const [district, setDistrict] = useState<string>(initialSaved?.district || "Nagpur");
  const [districts, setDistricts] = useState<string[]>(MAHARASHTRA_DISTRICTS_FALLBACK);

  // Crop & Quantity
  const [commodity, setCommodity] = useState<string>(initialSaved?.commodity || "Wheat");
  const [quantity, setQuantity] = useState<string>(
    initialSaved?.quantity ? String(initialSaved.quantity) : "10"
  );

  // Vehicle
  const [vehicle, setVehicle] = useState<string>(initialSaved?.vehicle || "pickup");
  const [vehicles, setVehicles] = useState<Record<string, VehicleSpec>>(DEFAULT_VEHICLES);

  // Quality Grade: "Good" | "Average" | "Below average" | "Poor" | "custom"
  const [qualityGrade, setQualityGrade] = useState<string>(initialSaved?.qualityGrade || "Good");
  const [customPct, setCustomPct] = useState<string>(
    initialSaved?.customPct ? String(initialSaved.customPct) : "0"
  );

  // Advanced Overrides
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [marketFeePct, setMarketFeePct] = useState("1.0");
  const [commissionPct, setCommissionPct] = useState("2.0");
  const [ratePerKm, setRatePerKm] = useState(
    DEFAULT_VEHICLES[initialSaved?.vehicle || "pickup"]?.rate_per_km.toFixed(1) || "18.0"
  );
  const [includeOtherCharges, setIncludeOtherCharges] = useState(false);

  // Validation Errors
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Fetch live metadata (districts and vehicles)
  useEffect(() => {
    let active = true;
    api
      .getDistricts(state)
      .then((res) => {
        if (active && res.districts && res.districts.length > 0) {
          setDistricts(res.districts);
        }
      })
      .catch(() => {
        // Fallback already pre-set
      });

    api
      .getVehicles()
      .then((res) => {
        if (active && res.vehicles && Object.keys(res.vehicles).length > 0) {
          setVehicles(res.vehicles);
        }
      })
      .catch(() => {
        // Fallback already pre-set
      });

    return () => {
      active = false;
    };
  }, [state]);

  const handleVehicleChange = (newVehicle: string) => {
    setVehicle(newVehicle);
    if (vehicles[newVehicle]) {
      setRatePerKm(vehicles[newVehicle].rate_per_km.toFixed(1));
    }
  };

  // Quick Chips handler
  const handleQuickQuantity = (q: number) => {
    setQuantity(String(q));
    if (errors.quantity) {
      setErrors((prev) => ({ ...prev, quantity: "" }));
    }
  };

  // Validate inputs
  const validate = useCallback((): boolean => {
    const errs: Record<string, string> = {};

    if (mode === "pincode") {
      const pinRegex = /^[1-9][0-9]{5}$/;
      if (!pincode || !pinRegex.test(pincode.trim())) {
        errs.pincode = t("search.validation.invalidPincode");
      }
    } else {
      if (!district) {
        errs.district = t("search.validation.selectDistrict");
      }
    }

    if (!commodity) {
      errs.commodity = t("search.validation.selectCrop");
    }

    const qtyNum = parseFloat(quantity);
    if (isNaN(qtyNum) || qtyNum <= 0) {
      errs.quantity = t("search.validation.invalidQuantity");
    }

    if (qualityGrade === "custom") {
      const cutNum = parseFloat(customPct);
      if (isNaN(cutNum) || cutNum < 0 || cutNum > 30) {
        errs.customPct = t("search.validation.invalidCustomPct");
      }
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  }, [mode, pincode, district, commodity, quantity, qualityGrade, customPct, t]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    const requestBody: CompareRequest = {
      commodity,
      quantity_quintals: parseFloat(quantity),
      vehicle,
      quality:
        qualityGrade === "custom"
          ? { custom_pct: parseFloat(customPct) }
          : { grade: qualityGrade },
      price_basis: "modal",
      include_other_charges: includeOtherCharges,
      limit: 5,
    };

    if (mode === "pincode") {
      requestBody.pincode = pincode.trim();
    } else {
      requestBody.state = state;
      requestBody.district = district;
    }

    // Overrides if customized
    const overrides: Record<string, number> = {};
    const mf = parseFloat(marketFeePct);
    const cf = parseFloat(commissionPct);
    const rk = parseFloat(ratePerKm);

    if (!isNaN(mf) && mf !== 1.0) overrides.market_fee_pct = mf;
    if (!isNaN(cf) && cf !== 2.0) overrides.commission_pct = cf;
    if (!isNaN(rk) && rk !== (vehicles[vehicle]?.rate_per_km ?? 18)) {
      overrides.rate_per_km = rk;
    }

    if (Object.keys(overrides).length > 0) {
      requestBody.overrides = overrides;
    }

    // Persist to localStorage
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          mode,
          pincode,
          state,
          district,
          commodity,
          quantity,
          vehicle,
          qualityGrade,
          customPct,
        })
      );
    } catch {
      // ignore
    }

    onSearch(requestBody);
  };

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="glass p-5 sm:p-7 flex flex-col gap-5 w-full shadow-md"
      aria-label="Mandi Arbitrage Search Panel"
    >
      {/* 1. Location Mode Toggle */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-glass-border/30 pb-4">
        <div className="flex items-center gap-1.5 p-1 bg-black/5 dark:bg-white/5 rounded-full border border-glass-border/40">
          <button
            type="button"
            onClick={() => setMode("pincode")}
            className={`px-3 py-1 text-xs font-semibold rounded-full transition-all duration-200 cursor-pointer ${
              mode === "pincode"
                ? "bg-forest text-white shadow-sm"
                : "text-ink-muted hover:text-ink"
            }`}
            aria-pressed={mode === "pincode"}
          >
            {t("search.modePincode")}
          </button>
          <button
            type="button"
            onClick={() => setMode("district")}
            className={`px-3 py-1 text-xs font-semibold rounded-full transition-all duration-200 cursor-pointer ${
              mode === "district"
                ? "bg-forest text-white shadow-sm"
                : "text-ink-muted hover:text-ink"
            }`}
            aria-pressed={mode === "district"}
          >
            {t("search.modeDistrict")}
          </button>
        </div>

        {/* Assumptions link badge */}
        <Link
          href="/methodology"
          className="inline-flex items-center gap-1.5 text-xs text-wheat-ink hover:underline font-medium"
        >
          <Info className="w-3.5 h-3.5" />
          <span>{t("search.assumptionsBadge")}</span>
        </Link>
      </div>

      {/* 2. Location Input */}
      {mode === "pincode" ? (
        <div className="flex flex-col gap-1.5">
          <label htmlFor="pincode-input" className="text-xs font-semibold text-ink">
            {t("search.pincode")}
          </label>
          <input
            id="pincode-input"
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            maxLength={6}
            value={pincode}
            onChange={(e) => {
              setPincode(e.target.value.replace(/\D/g, ""));
              if (errors.pincode) setErrors((prev) => ({ ...prev, pincode: "" }));
            }}
            placeholder="e.g. 440001"
            className="glass-strong card-inner-input px-4 py-2.5 text-sm text-ink font-mono focus-visible:outline-none"
            aria-invalid={!!errors.pincode}
            aria-describedby={errors.pincode ? "pincode-error" : undefined}
          />
          {errors.pincode && (
            <p id="pincode-error" className="text-xs text-clay font-medium mt-0.5">
              {errors.pincode}
            </p>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="state-select" className="text-xs font-semibold text-ink">
              {t("search.state")}
            </label>
            <select
              id="state-select"
              value={state}
              onChange={(e) => setState(e.target.value)}
              className="glass-strong card-inner-input px-3.5 py-2.5 text-sm text-ink focus-visible:outline-none"
            >
              <option value="Maharashtra">Maharashtra</option>
            </select>
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="district-select" className="text-xs font-semibold text-ink">
              {t("search.district")}
            </label>
            <select
              id="district-select"
              value={district}
              onChange={(e) => {
                setDistrict(e.target.value);
                if (errors.district) setErrors((prev) => ({ ...prev, district: "" }));
              }}
              className="glass-strong card-inner-input px-3.5 py-2.5 text-sm text-ink focus-visible:outline-none"
              aria-invalid={!!errors.district}
              aria-describedby={errors.district ? "district-error" : undefined}
            >
              <option value="">{t("search.selectDistrict")}</option>
              {districts.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
            {errors.district && (
              <p id="district-error" className="text-xs text-clay font-medium mt-0.5">
                {errors.district}
              </p>
            )}
          </div>
        </div>
      )}

      {/* 3. Crop & Quantity Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Crop Select */}
        <div className="flex flex-col gap-1.5">
          <label htmlFor="crop-select" className="text-xs font-semibold text-ink">
            {t("search.crop")}
          </label>
          <select
            id="crop-select"
            value={commodity}
            onChange={(e) => {
              setCommodity(e.target.value);
              if (errors.commodity) setErrors((prev) => ({ ...prev, commodity: "" }));
            }}
            className="glass-strong card-inner-input px-3.5 py-2.5 text-sm text-ink focus-visible:outline-none"
          >
            {CROPS.map((c) => (
              <option key={c.id} value={c.id}>
                {lang === "hi"
                  ? `${t(`crops.${c.key}`)} (${c.id})`
                  : `${c.id} (${t(`crops.${c.key}`)})`}
              </option>
            ))}
          </select>
        </div>

        {/* Quantity & Quick Chips */}
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <label htmlFor="quantity-input" className="text-xs font-semibold text-ink">
              {t("search.quantity")}
            </label>
            {/* Quick Chips */}
            <div className="flex items-center gap-1">
              {[5, 10, 25, 50].map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => handleQuickQuantity(q)}
                  className={`px-2 py-0.5 text-[11px] rounded-full border transition-all cursor-pointer ${
                    quantity === String(q)
                      ? "bg-forest/15 border-forest text-forest font-semibold"
                      : "bg-black/5 dark:bg-white/5 border-glass-border/40 text-ink-muted hover:text-ink"
                  }`}
                >
                  {q}q
                </button>
              ))}
            </div>
          </div>
          <input
            id="quantity-input"
            type="number"
            min="0.1"
            step="0.5"
            value={quantity}
            onChange={(e) => {
              setQuantity(e.target.value);
              if (errors.quantity) setErrors((prev) => ({ ...prev, quantity: "" }));
            }}
            placeholder="10"
            className="glass-strong card-inner-input px-4 py-2 text-sm text-ink font-mono focus-visible:outline-none"
            aria-invalid={!!errors.quantity}
            aria-describedby={errors.quantity ? "quantity-error" : undefined}
          />
          {errors.quantity && (
            <p id="quantity-error" className="text-xs text-clay font-medium mt-0.5">
              {errors.quantity}
            </p>
          )}
        </div>
      </div>

      {/* 4. Vehicle Selection */}
      <div className="flex flex-col gap-1.5">
        <label htmlFor="vehicle-select" className="text-xs font-semibold text-ink">
          {t("search.vehicle")}
        </label>
        <select
          id="vehicle-select"
          value={vehicle}
          onChange={(e) => handleVehicleChange(e.target.value)}
          className="glass-strong card-inner-input px-3.5 py-2.5 text-sm text-ink focus-visible:outline-none"
        >
          {Object.entries(vehicles).map(([k, v]) => (
            <option key={k} value={k}>
              {t(`vehicles.${k}`, `${k} (${v.capacity_q} q)`)} - ₹{v.rate_per_km}/km
            </option>
          ))}
        </select>
      </div>

      {/* 5. Quality Grade Segmented Control */}
      <div className="flex flex-col gap-2">
        <label className="text-xs font-semibold text-ink">
          {t("search.quality")}
        </label>
        <div
          role="radiogroup"
          aria-label={t("search.quality")}
          className="grid grid-cols-2 sm:grid-cols-5 gap-1.5 p-1 bg-black/5 dark:bg-white/5 rounded-2xl border border-glass-border/40"
        >
          {[
            { id: "Good", key: "good" },
            { id: "Average", key: "average" },
            { id: "Below average", key: "below_average" },
            { id: "Poor", key: "poor" },
            { id: "custom", key: "custom" },
          ].map((grade) => (
            <button
              key={grade.id}
              type="button"
              role="radio"
              aria-checked={qualityGrade === grade.id}
              onClick={() => {
                setQualityGrade(grade.id);
                if (errors.customPct) setErrors((prev) => ({ ...prev, customPct: "" }));
              }}
              className={`py-2 px-2 text-xs font-medium rounded-xl text-center transition-all cursor-pointer ${
                qualityGrade === grade.id
                  ? "bg-forest text-white shadow-sm font-semibold"
                  : "text-ink-muted hover:text-ink"
              }`}
            >
              {t(`quality.${grade.key}`)}
            </button>
          ))}
        </div>

        {/* Custom Percentage Input */}
        {qualityGrade === "custom" && (
          <div className="flex items-center gap-3 mt-1.5 animate-fadeIn">
            <label htmlFor="custom-pct-input" className="text-xs font-medium text-ink-muted whitespace-nowrap">
              {t("search.customPctLabel")}:
            </label>
            <input
              id="custom-pct-input"
              type="number"
              min="0"
              max="30"
              step="0.5"
              value={customPct}
              onChange={(e) => {
                setCustomPct(e.target.value);
                if (errors.customPct) setErrors((prev) => ({ ...prev, customPct: "" }));
              }}
              className="glass-strong card-inner-input px-3 py-1.5 w-24 text-sm text-ink font-mono focus-visible:outline-none"
              aria-invalid={!!errors.customPct}
              aria-describedby={errors.customPct ? "custom-pct-error" : undefined}
            />
            {errors.customPct && (
              <p id="custom-pct-error" className="text-xs text-clay font-medium">
                {errors.customPct}
              </p>
            )}
          </div>
        )}
      </div>

      {/* 6. Advanced Overrides (Collapsible Accordion) */}
      <div className="border-t border-glass-border/30 pt-3">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center justify-between w-full py-1 text-xs font-semibold text-ink-muted hover:text-forest transition-colors cursor-pointer"
          aria-expanded={showAdvanced}
        >
          <span>{t("search.advanced")}</span>
          {showAdvanced ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>

        {showAdvanced && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 animate-fadeIn">
            <div className="flex flex-col gap-1">
              <label htmlFor="market-fee-input" className="text-[11px] font-medium text-ink-muted">
                {t("search.marketFee")}
              </label>
              <input
                id="market-fee-input"
                type="number"
                step="0.05"
                min="0"
                value={marketFeePct}
                onChange={(e) => setMarketFeePct(e.target.value)}
                className="glass-strong card-inner-input px-3 py-1.5 text-xs text-ink font-mono focus-visible:outline-none"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label htmlFor="commission-input" className="text-[11px] font-medium text-ink-muted">
                {t("search.commission")}
              </label>
              <input
                id="commission-input"
                type="number"
                step="0.1"
                min="0"
                value={commissionPct}
                onChange={(e) => setCommissionPct(e.target.value)}
                className="glass-strong card-inner-input px-3 py-1.5 text-xs text-ink font-mono focus-visible:outline-none"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label htmlFor="rate-km-input" className="text-[11px] font-medium text-ink-muted">
                {t("search.ratePerKm")}
              </label>
              <input
                id="rate-km-input"
                type="number"
                step="1"
                min="1"
                value={ratePerKm}
                onChange={(e) => setRatePerKm(e.target.value)}
                className="glass-strong card-inner-input px-3 py-1.5 text-xs text-ink font-mono focus-visible:outline-none"
              />
            </div>

            <div className="sm:col-span-3 flex items-center gap-2 pt-1">
              <input
                id="other-charges-toggle"
                type="checkbox"
                checked={includeOtherCharges}
                onChange={(e) => setIncludeOtherCharges(e.target.checked)}
                className="rounded accent-forest w-4 h-4 cursor-pointer"
              />
              <label htmlFor="other-charges-toggle" className="text-xs text-ink cursor-pointer select-none">
                {t("search.includeOtherCharges")}
              </label>
            </div>
          </div>
        )}
      </div>

      {/* 7. Submit Button */}
      <button
        type="submit"
        disabled={isLoading}
        className="glass glass-pill bg-forest hover:bg-forest-strong text-black dark:text-white font-semibold py-3 px-6 text-sm tracking-wide shadow-md transition-all duration-200 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-2"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin text-black dark:text-white" />
            <span>{t("search.loading")}</span>
          </>
        ) : (
          <span>{t("search.submit")}</span>
        )}
      </button>
    </form>
  );
}
