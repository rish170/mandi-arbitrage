"use client";

import React from "react";
import { useI18n } from "@/lib/i18n";
import { CompareResultItem } from "@/lib/api";
import { formatCurrency } from "@/lib/format";

interface CostBreakdownProps {
  results: CompareResultItem[];
}

export function CostBreakdown({ results }: CostBreakdownProps) {
  const { t } = useI18n();

  return (
    <div
      role="region"
      aria-label="Cost Breakdown Comparison"
      className="glass p-5 sm:p-7 flex flex-col gap-5 shadow-sm"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-glass-border/30 pb-3">
        <h3 className="text-base font-bold text-ink">
          {t("results.breakdown")}
        </h3>
        {/* Legend */}
        <div className="flex items-center gap-3 text-xs flex-wrap">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-forest inline-block" />
            <span className="text-ink font-medium">{t("results.netRealization")}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-clay inline-block" />
            <span className="text-ink font-medium">{t("results.mandiFee")}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-soil inline-block" />
            <span className="text-ink font-medium">{t("results.transportCost")}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-wheat inline-block" />
            <span className="text-ink font-medium">{t("results.qualityCut")}</span>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-4">
        {results.map((item) => {
          const gross = parseFloat(item.breakdown.price_q) || 1;
          const net = Math.max(0, parseFloat(item.breakdown.net_q));
          const fee = parseFloat(item.breakdown.mandi_fee_q);
          const transport = parseFloat(item.breakdown.transport_q);
          const qualityCut = parseFloat(item.breakdown.quality_cut_q);

          const netPct = Math.min(100, (net / gross) * 100);
          const feePct = (fee / gross) * 100;
          const transPct = (transport / gross) * 100;
          const cutPct = (qualityCut / gross) * 100;

          return (
            <div key={item.mandi.id} className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-ink">
                  #{item.rank} {item.mandi.name}
                </span>
                <span className="tabular-nums font-semibold text-ink">
                  {formatCurrency(item.breakdown.price_q)} / q
                </span>
              </div>

              {/* Stacked Horizontal Bar */}
              <div
                className="w-full h-5 rounded-full overflow-hidden flex bg-black/5 dark:bg-white/5 border border-glass-border/40"
                role="progressbar"
                aria-valuenow={Math.round(netPct)}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`Realization breakdown for ${item.mandi.name}: Net ${netPct.toFixed(1)}%, Fee ${feePct.toFixed(1)}%, Transport ${transPct.toFixed(1)}%`}
              >
                {/* Net Realization */}
                <div
                  style={{ width: `${netPct}%` }}
                  className="bg-forest h-full transition-all duration-300"
                  title={`Net Realization: ${formatCurrency(item.breakdown.net_q)} (${netPct.toFixed(1)}%)`}
                />
                {/* APMC Fee */}
                <div
                  style={{ width: `${feePct}%` }}
                  className="bg-clay h-full transition-all duration-300"
                  title={`Mandi Fee: ${formatCurrency(item.breakdown.mandi_fee_q)} (${feePct.toFixed(1)}%)`}
                />
                {/* Transport Cost */}
                <div
                  style={{ width: `${transPct}%` }}
                  className="bg-soil h-full transition-all duration-300"
                  title={`Transport Cost: ${formatCurrency(item.breakdown.transport_q)} (${transPct.toFixed(1)}%)`}
                />
                {/* Quality Cut */}
                {cutPct > 0 && (
                  <div
                    style={{ width: `${cutPct}%` }}
                    className="bg-wheat h-full transition-all duration-300"
                    title={`Quality Cut: ${formatCurrency(item.breakdown.quality_cut_q)} (${cutPct.toFixed(1)}%)`}
                  />
                )}
              </div>

              {/* Accessible Summary Line for Readers */}
              <div className="sr-only">
                {item.mandi.name}: Gross {formatCurrency(item.breakdown.price_q)}, Net {formatCurrency(item.breakdown.net_q)}, APMC Fee {formatCurrency(item.breakdown.mandi_fee_q)}, Transport {formatCurrency(item.breakdown.transport_q)}.
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
