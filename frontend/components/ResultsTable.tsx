"use client";

import React, { useState } from "react";
import { ArrowUpDown, Crown, MapPin, AlertCircle } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { CompareResultItem } from "@/lib/api";
import { formatCurrency, formatDistance } from "@/lib/format";

interface ResultsTableProps {
  results: CompareResultItem[];
}

type SortField = "rank" | "net_q" | "road_km" | "price_q";
type SortDirection = "asc" | "desc";

export function ResultsTable({ results }: ResultsTableProps) {
  const { t } = useI18n();

  const [sortField, setSortField] = useState<SortField>("rank");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection(field === "rank" || field === "road_km" ? "asc" : "desc");
    }
  };

  const sortedResults = [...results].sort((a, b) => {
    let diff = 0;
    if (sortField === "rank") {
      diff = a.rank - b.rank;
    } else if (sortField === "net_q") {
      diff = parseFloat(a.breakdown.net_q) - parseFloat(b.breakdown.net_q);
    } else if (sortField === "road_km") {
      diff = a.distance.road_km - b.distance.road_km;
    } else if (sortField === "price_q") {
      diff = parseFloat(a.breakdown.price_q) - parseFloat(b.breakdown.price_q);
    }
    return sortDirection === "asc" ? diff : -diff;
  });

  return (
    <div className="w-full flex flex-col gap-3">
      {/* Desktop Table View (>= 768px) */}
      <div className="hidden md:block overflow-x-auto rounded-2xl border border-glass-border/40 shadow-sm">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-glass-border/40 bg-black/5 dark:bg-white/5 text-ink-muted uppercase tracking-wider font-semibold">
              <th
                scope="col"
                className="py-3 px-3 cursor-pointer select-none hover:text-ink"
                onClick={() => handleSort("rank")}
              >
                <div className="flex items-center gap-1">
                  <span>{t("results.rank")}</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th scope="col" className="py-3 px-3">
                {t("results.mandi")}
              </th>
              <th
                scope="col"
                className="py-3 px-3 cursor-pointer select-none hover:text-ink"
                onClick={() => handleSort("road_km")}
              >
                <div className="flex items-center gap-1">
                  <span>{t("results.distance")}</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                scope="col"
                className="py-3 px-3 cursor-pointer select-none hover:text-ink"
                onClick={() => handleSort("price_q")}
              >
                <div className="flex items-center gap-1">
                  <span>{t("results.price")}</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th scope="col" className="py-3 px-3 text-right">
                {t("results.mandiFee")}
              </th>
              <th scope="col" className="py-3 px-3 text-right">
                {t("results.transportCost")}
              </th>
              <th scope="col" className="py-3 px-3 text-right">
                {t("results.qualityCut")}
              </th>
              <th
                scope="col"
                className="py-3 px-3 text-right cursor-pointer select-none hover:text-ink"
                onClick={() => handleSort("net_q")}
              >
                <div className="flex items-center justify-end gap-1">
                  <span>{t("results.netPerQ")}</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th scope="col" className="py-3 px-3 text-right">
                {t("results.netTotal")}
              </th>
              <th scope="col" className="py-3 px-3 text-right">
                {t("results.deltaVsNearest")}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-glass-border/30">
            {sortedResults.map((item) => {
              const deltaNum = parseFloat(item.vs_nearest.delta_q);
              const isBest = item.rank === 1;

              return (
                <tr
                  key={item.mandi.id}
                  className={`glass-strong transition-colors hover:bg-forest/5 ${
                    isBest ? "bg-wheat/5 font-medium" : ""
                  }`}
                >
                  {/* Rank */}
                  <td className="py-3 px-3 tabular-nums font-semibold text-ink">
                    <div className="flex items-center gap-1.5">
                      {isBest ? (
                        <Crown className="w-4 h-4 text-wheat inline-block" />
                      ) : (
                        <span className="w-4 text-center">{item.rank}</span>
                      )}
                      {isBest && (
                        <span className="glass glass-pill px-1.5 py-0.2 text-[10px] font-bold text-wheat-ink border-wheat/30">
                          BEST
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Mandi & District */}
                  <td className="py-3 px-3">
                    <div className="flex flex-col">
                      <span className="font-semibold text-ink flex items-center gap-1">
                        {item.mandi.name}
                        {item.is_nearest && (
                          <span className="glass glass-pill px-1.5 text-[10px] text-forest font-semibold border-forest/30">
                            {t("results.nearestBadge")}
                          </span>
                        )}
                      </span>
                      <span className="text-[11px] text-ink-muted">
                        {item.mandi.district}, {item.mandi.state}
                      </span>
                    </div>
                  </td>

                  {/* Distance */}
                  <td className="py-3 px-3 tabular-nums whitespace-nowrap">
                    <div className="flex flex-col">
                      <span className="text-ink font-medium">
                        {formatDistance(item.distance.road_km)}
                      </span>
                      {item.distance.source === "haversine_fallback" && (
                        <span className="text-[10px] text-clay font-medium inline-flex items-center gap-0.5">
                          <AlertCircle className="w-2.5 h-2.5" />
                          {t("results.fallbackTag")}
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Mandi Modal Price */}
                  <td className="py-3 px-3 tabular-nums whitespace-nowrap">
                    <div className="flex flex-col">
                      <span className="text-ink font-semibold">
                        {formatCurrency(item.price.value)}
                      </span>
                      <span className="text-[10px] text-ink-muted">
                        {item.price.arrival_date}
                        {item.price.is_stale && (
                          <span className="ml-1 text-clay font-medium">
                            ({t("results.staleTag")})
                          </span>
                        )}
                      </span>
                    </div>
                  </td>

                  {/* Mandi Fee */}
                  <td className="py-3 px-3 text-right tabular-nums text-clay font-medium">
                    -{formatCurrency(item.breakdown.mandi_fee_q)}
                  </td>

                  {/* Transport Cost */}
                  <td className="py-3 px-3 text-right tabular-nums text-clay font-medium">
                    -{formatCurrency(item.breakdown.transport_q)}
                  </td>

                  {/* Quality Cut */}
                  <td className="py-3 px-3 text-right tabular-nums text-soil font-medium">
                    {parseFloat(item.breakdown.quality_cut_q) > 0
                      ? `-${formatCurrency(item.breakdown.quality_cut_q)}`
                      : "₹0.00"}
                  </td>

                  {/* NET per quintal */}
                  <td className="py-3 px-3 text-right tabular-nums font-bold text-forest text-sm">
                    {formatCurrency(item.breakdown.net_q)}
                  </td>

                  {/* Net Total */}
                  <td className="py-3 px-3 text-right tabular-nums font-bold text-ink">
                    {formatCurrency(item.breakdown.net_total)}
                  </td>

                  {/* Delta vs Nearest */}
                  <td className="py-3 px-3 text-right tabular-nums font-semibold whitespace-nowrap">
                    {item.is_nearest ? (
                      <span className="text-ink-muted font-normal text-[11px]">
                        — ({t("results.nearestBadge")})
                      </span>
                    ) : deltaNum > 0 ? (
                      <span className="text-forest">
                        +{formatCurrency(item.vs_nearest.delta_q)}
                      </span>
                    ) : (
                      <span className="text-clay">
                        {formatCurrency(item.vs_nearest.delta_q)}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Mobile Stacked Glass Cards (< 768px) */}
      <div className="md:hidden flex flex-col gap-3">
        {sortedResults.map((item) => {
          const deltaNum = parseFloat(item.vs_nearest.delta_q);
          const isBest = item.rank === 1;

          return (
            <div
              key={item.mandi.id}
              className={`glass p-4 flex flex-col gap-3 border ${
                isBest ? "border-wheat/40 bg-wheat/5" : "border-glass-border/40"
              }`}
            >
              {/* Card Header: Rank & Mandi Name */}
              <div className="flex items-start justify-between gap-2 border-b border-glass-border/30 pb-2.5">
                <div className="flex flex-col">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {isBest && <Crown className="w-4 h-4 text-wheat inline-block" />}
                    <span className="font-bold text-base text-ink">{item.mandi.name}</span>
                    {isBest && (
                      <span className="glass glass-pill px-1.5 text-[10px] font-bold text-wheat-ink border-wheat/30">
                        {t("results.bestBadge")}
                      </span>
                    )}
                    {item.is_nearest && (
                      <span className="glass glass-pill px-1.5 text-[10px] text-forest font-semibold border-forest/30">
                        {t("results.nearestBadge")}
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-ink-muted">
                    {item.mandi.district}, {item.mandi.state}
                  </span>
                </div>
                <div className="text-right flex flex-col items-end">
                  <span className="text-xs font-semibold text-ink-muted">Rank #{item.rank}</span>
                  <span className="text-xs text-ink-muted flex items-center gap-0.5">
                    <MapPin className="w-3 h-3" />
                    {formatDistance(item.distance.road_km)}
                  </span>
                </div>
              </div>

              {/* Card Body: Modal Price & NET Realization */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-ink-muted block">{t("results.grossPrice")}</span>
                  <span className="font-semibold text-ink tabular-nums">
                    {formatCurrency(item.price.value)}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-ink-muted block">{t("results.netPerQ")}</span>
                  <span className="font-bold text-forest text-sm tabular-nums">
                    {formatCurrency(item.breakdown.net_q)}
                  </span>
                </div>
                <div>
                  <span className="text-ink-muted block">{t("results.mandiFee")} + Transport</span>
                  <span className="text-clay tabular-nums font-medium">
                    -{formatCurrency(parseFloat(item.breakdown.mandi_fee_q) + parseFloat(item.breakdown.transport_q))}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-ink-muted block">{t("results.netTotal")}</span>
                  <span className="font-bold text-ink tabular-nums">
                    {formatCurrency(item.breakdown.net_total)}
                  </span>
                </div>
              </div>

              {/* Delta vs Nearest */}
              {!item.is_nearest && (
                <div className="bg-black/5 dark:bg-white/5 rounded-xl px-3 py-1.5 flex items-center justify-between text-xs font-medium">
                  <span className="text-ink-muted">{t("results.deltaVsNearest")}:</span>
                  <span className={deltaNum > 0 ? "text-forest font-bold" : "text-clay font-bold"}>
                    {deltaNum > 0 ? `+${formatCurrency(item.vs_nearest.delta_q)}` : formatCurrency(item.vs_nearest.delta_q)} / q
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
