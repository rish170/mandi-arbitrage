"use client";

import React, { useEffect, useState, useMemo } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { useTheme } from "next-themes";
import { useI18n } from "@/lib/i18n";
import { api, MandiTrendSeries } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import { Loader2 } from "lucide-react";

interface TrendChartProps {
  mandiIds: number[];
  bestMandiId: number;
  commodity: string;
}

export function TrendChart({ mandiIds, bestMandiId, commodity }: TrendChartProps) {
  const { t } = useI18n();
  const { resolvedTheme } = useTheme();

  const [seriesList, setSeriesList] = useState<MandiTrendSeries[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [hiddenMandiIds, setHiddenMandiIds] = useState<Record<number, boolean>>({});

  const isDark = resolvedTheme === "dark";

  // Palette series colors (forest, wheat, clay, olive, soil)
  const PALETTE_COLORS = useMemo(
    () => [
      isDark ? "#58B874" : "#1F5C3B", // Forest
      isDark ? "#E2B54F" : "#C9962B", // Wheat
      isDark ? "#E0805A" : "#B4532A", // Clay
      "#7A8B2E",                     // Olive
      isDark ? "#A98B72" : "#6B4F3A", // Soil
    ],
    [isDark]
  );

  useEffect(() => {
    if (!mandiIds || mandiIds.length === 0 || !commodity) {
      return;
    }

    let active = true;
    Promise.resolve().then(() => {
      if (active) {
        setLoading(true);
        setError(false);
      }
    });

    api
      .getTrend(mandiIds, commodity, 7)
      .then((res) => {
        if (active) {
          setSeriesList(res.series || []);
          setLoading(false);
        }
      })
      .catch(() => {
        if (active) {
          setError(true);
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [mandiIds, commodity]);

  // Transform series list into pivoted tabular data for Recharts: [{ date: "10 Oct", "mandi_1": 2900, ... }]
  const { chartData, hasSeededData } = useMemo(() => {
    if (!seriesList || seriesList.length === 0) {
      return { chartData: [], hasSeededData: false };
    }

    const dateMap: Record<string, Record<string, number | null>> = {};
    let foundSeeded = false;

    // Collect all dates
    seriesList.forEach((s) => {
      s.points.forEach((p) => {
        if (p.is_seeded) foundSeeded = true;
        if (!dateMap[p.date]) {
          dateMap[p.date] = {};
        }
        const val = p.modal ? parseFloat(p.modal) : null;
        dateMap[p.date][`mandi_${s.mandi_id}`] = val;
      });
    });

    const datesSorted = Object.keys(dateMap).sort();
    const data = datesSorted.map((d) => {
      // Format date for X-axis label e.g. "12 Oct"
      let formattedDate = d;
      try {
        const parts = d.split("-");
        if (parts.length === 3) {
          const dateObj = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
          formattedDate = dateObj.toLocaleDateString("en-IN", { month: "short", day: "numeric" });
        }
      } catch {
        // fallback
      }
      return {
        date: formattedDate,
        ...dateMap[d],
      };
    });

    return { chartData: data, hasSeededData: foundSeeded };
  }, [seriesList]);

  const toggleMandiVisibility = (id: number) => {
    setHiddenMandiIds((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const gridColor = isDark ? "rgba(255, 255, 255, 0.08)" : "rgba(23, 74, 47, 0.08)";
  const textColor = isDark ? "#97A89B" : "#56685A";

  if (loading) {
    return (
      <div className="glass p-8 flex flex-col items-center justify-center gap-3 min-h-[260px] text-ink-muted">
        <Loader2 className="w-5 h-5 animate-spin text-forest" />
        <span className="text-xs">{t("states.loading")}</span>
      </div>
    );
  }

  if (error || chartData.length === 0) {
    return (
      <div className="glass p-6 text-center text-xs text-ink-muted min-h-[160px] flex items-center justify-center">
        {t("trend.noData")}
      </div>
    );
  }

  return (
    <div
      role="region"
      aria-label="7-Day Mandi Price Trend Chart"
      className="glass p-5 sm:p-7 flex flex-col gap-4 shadow-sm"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-glass-border/30 pb-3">
        <div>
          <h3 className="text-base font-bold text-ink">{t("trend.title")}</h3>
          <p className="text-xs text-ink-muted">{t("trend.subtitle")}</p>
        </div>

        {hasSeededData && (
          <span className="text-[11px] text-wheat-ink font-medium bg-wheat/10 px-2.5 py-1 rounded-full border border-wheat/30 w-fit">
            {t("trend.seededNote")}
          </span>
        )}
      </div>

      {/* Interactive Legend Chips to Toggle Series */}
      <div className="flex items-center gap-2 flex-wrap">
        {seriesList.map((s, idx) => {
          const isBest = s.mandi_id === bestMandiId;
          const color = PALETTE_COLORS[idx % PALETTE_COLORS.length];
          const isHidden = hiddenMandiIds[s.mandi_id];

          return (
            <button
              key={s.mandi_id}
              type="button"
              onClick={() => toggleMandiVisibility(s.mandi_id)}
              className={`glass glass-pill px-3 py-1 text-xs font-semibold flex items-center gap-2 cursor-pointer transition-all ${
                isHidden ? "opacity-40" : "opacity-100"
              }`}
              style={{
                borderColor: color,
              }}
              aria-pressed={!isHidden}
            >
              <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: color }} />
              <span className="text-ink">
                {s.mandi_name} {isBest && "★"}
              </span>
            </button>
          );
        })}
      </div>

      {/* Recharts Container */}
      <div className="w-full h-64 sm:h-72 mt-2">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
            <XAxis
              dataKey="date"
              stroke={textColor}
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: gridColor }}
            />
            <YAxis
              stroke={textColor}
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: gridColor }}
              domain={["auto", "auto"]}
              tickFormatter={(val) => `₹${val}`}
            />
            <Tooltip
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="glass-strong p-3 rounded-xl shadow-lg border border-glass-border/60 text-xs flex flex-col gap-1.5 backdrop-blur-md">
                      <span className="font-bold text-ink border-b border-glass-border/30 pb-1">
                        {label}
                      </span>
                      {payload.map((entry, idx) => {
                        const mandiKey = String(entry.dataKey || "");
                        const mandiId = parseInt(mandiKey.replace("mandi_", ""));
                        const seriesObj = seriesList.find((s) => s.mandi_id === mandiId);
                        const name = seriesObj ? seriesObj.mandi_name : entry.name;
                        return (
                          <div key={idx} className="flex items-center justify-between gap-4">
                            <span className="flex items-center gap-1.5 text-ink font-medium">
                              <span
                                className="w-2 h-2 rounded-full inline-block"
                                style={{ backgroundColor: entry.color }}
                              />
                              {name}:
                            </span>
                            <span className="font-bold text-forest tabular-nums">
                              {entry.value !== null && entry.value !== undefined
                                ? formatCurrency(entry.value as number)
                                : "Closed"}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  );
                }
                return null;
              }}
            />
            {seriesList.map((s, idx) => {
              const isBest = s.mandi_id === bestMandiId;
              const color = PALETTE_COLORS[idx % PALETTE_COLORS.length];
              const isHidden = hiddenMandiIds[s.mandi_id];
              const hasSeededInSeries = s.points.some((p) => p.is_seeded);

              if (isHidden) return null;

              return (
                <Line
                  key={s.mandi_id}
                  type="monotone"
                  dataKey={`mandi_${s.mandi_id}`}
                  name={s.mandi_name}
                  stroke={color}
                  strokeWidth={isBest ? 3 : 1.75}
                  strokeDasharray={hasSeededInSeries ? "4 4" : undefined}
                  dot={{ r: isBest ? 4 : 2.5, fill: color }}
                  activeDot={{ r: 6 }}
                  connectNulls={false}
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
