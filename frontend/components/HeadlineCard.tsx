"use client";

import React from "react";
import { useI18n } from "@/lib/i18n";
import { CompareResponse } from "@/lib/api";
import { formatCurrency } from "@/lib/format";

interface HeadlineCardProps {
  data: CompareResponse;
}

export function HeadlineCard({ data }: HeadlineCardProps) {
  const { t, lang } = useI18n();

  const { results, summary, query } = data;
  if (!results || results.length === 0) return null;

  const bestResult = results.find((r) => r.mandi.id === summary.best_mandi_id) || results[0];
  const nearestResult =
    results.find((r) => r.mandi.id === summary.nearest_mandi_id) ||
    results.find((r) => r.is_nearest) ||
    results[0];

  const isBestNearest = bestResult.mandi.id === nearestResult.mandi.id;

  const bestName = bestResult.mandi.name;
  const nearestName = nearestResult.mandi.name;
  const extraQ = formatCurrency(summary.extra_profit_q);
  const extraTotal = formatCurrency(summary.extra_profit_total);
  const netQ = formatCurrency(bestResult.breakdown.net_q);
  const netTotal = formatCurrency(bestResult.breakdown.net_total);
  const quantity = String(query.quantity_quintals || "10");

  return (
    <div
      role="region"
      aria-label="Profit Summary Headline"
      className="glass p-5 sm:p-7 border-l-4 border-l-wheat border-wheat/20 shadow-md flex flex-col gap-2"
    >
      <div className="flex items-center gap-2">
        <span className="glass glass-pill px-2.5 py-0.5 text-[11px] font-bold tracking-wide uppercase text-wheat-ink bg-wheat/10 border-wheat/30">
          {t("results.bestBadge")}
        </span>
      </div>

      <p className="text-base sm:text-xl lg:text-2xl text-ink leading-snug font-medium">
        {isBestNearest ? (
          lang === "hi" ? (
            <>
              <span className="font-hindi-serif font-bold text-forest">{bestName}</span>{" "}
              ही आपकी सबसे नजदीकी मंडी है और आपको प्रति क्विंटल{" "}
              <span className="font-display font-bold text-forest">{netQ}</span> (कुल{" "}
              <span className="font-display font-bold text-forest">{netTotal}</span>) का
              अधिकतम शुद्ध मुनाफा देती है।
            </>
          ) : (
            <>
              <span className="font-display font-bold text-forest">{bestName}</span> is both your
              nearest mandi and gives your highest net profit of{" "}
              <span className="font-display font-bold text-forest">{netQ}</span> per quintal (
              <span className="font-display font-bold text-forest">{netTotal}</span> total).
            </>
          )
        ) : lang === "hi" ? (
          <>
            <span className="font-hindi-serif font-bold text-ink-muted">{nearestName}</span> के बजाय{" "}
            <span className="font-hindi-serif font-bold text-forest">{bestName}</span> में बेचने पर आपको
            प्रति क्विंटल <span className="font-display font-bold text-forest">{extraQ}</span> अधिक
            मिलेंगे (आपके {quantity} क्विंटल पर कुल{" "}
            <span className="font-display font-bold text-forest">{extraTotal}</span> का फायदा)।
          </>
        ) : (
          <>
            Selling at <span className="font-display font-bold text-forest">{bestName}</span>{" "}
            instead of <span className="font-display font-bold text-ink-muted">{nearestName}</span>{" "}
            earns you <span className="font-display font-bold text-forest">{extraQ}</span> more per
            quintal (<span className="font-display font-bold text-forest">{extraTotal}</span> on your{" "}
            {quantity} quintals).
          </>
        )}
      </p>
    </div>
  );
}
