"use client";

import React, { useState, useEffect, useRef } from "react";
import { useI18n } from "@/lib/i18n";
import { SearchPanel } from "@/components/SearchPanel";
import { HeadlineCard } from "@/components/HeadlineCard";
import { ResultsTable } from "@/components/ResultsTable";
import { CostBreakdown } from "@/components/CostBreakdown";
import { TrendChart } from "@/components/TrendChart";
import { WarningsStrip } from "@/components/WarningsStrip";
import { SkeletonResults } from "@/components/SkeletonResults";
import { api, CompareRequest, CompareResponse } from "@/lib/api";
import { AlertCircle, RefreshCw, Clock } from "lucide-react";

export default function Home() {
  const { t, lang } = useI18n();

  const [isLoading, setIsLoading] = useState(false);
  const [showWakingUpMessage, setShowWakingUpMessage] = useState(false);
  const [resultsData, setResultsData] = useState<CompareResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lastRequest, setLastRequest] = useState<CompareRequest | null>(null);

  const wakingUpTimerRef = useRef<NodeJS.Timeout | null>(null);

  const handleSearch = async (req: CompareRequest) => {
    setIsLoading(true);
    setErrorMessage(null);
    setShowWakingUpMessage(false);
    setLastRequest(req);

    // After 4s, show a calm "backend waking up" message for Railway cold start
    if (wakingUpTimerRef.current) clearTimeout(wakingUpTimerRef.current);
    wakingUpTimerRef.current = setTimeout(() => {
      setShowWakingUpMessage(true);
    }, 4000);

    try {
      const response = await api.compareMandis(req);
      setResultsData(response);
    } catch (err: unknown) {
      const msg = (err as Error)?.message || t("states.error");
      setErrorMessage(msg);
    } finally {
      if (wakingUpTimerRef.current) clearTimeout(wakingUpTimerRef.current);
      setIsLoading(false);
      setShowWakingUpMessage(false);
    }
  };

  const handleRetry = () => {
    if (lastRequest) {
      handleSearch(lastRequest);
    }
  };

  useEffect(() => {
    return () => {
      if (wakingUpTimerRef.current) clearTimeout(wakingUpTimerRef.current);
    };
  }, []);

  const mandiIds = resultsData?.results.map((r) => r.mandi.id) || [];
  const bestMandiId = resultsData?.summary.best_mandi_id || 0;
  const commodity = String(resultsData?.query.commodity || "");

  return (
    <div className="w-full flex flex-col gap-6 pt-2 sm:pt-6">
      {/* Tool-First Header: Compact, Left-Aligned, Serif */}
      <header className="flex flex-col gap-1.5 max-w-2xl text-left">
        <h1
          className={`text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-ink ${
            lang === "hi" ? "font-hindi-serif" : "font-display"
          }`}
        >
          {t("brand.name")}
        </h1>
        <p className="text-sm sm:text-base text-ink-muted leading-relaxed">
          {t("brand.tagline")}
        </p>
      </header>

      {/* 1. Search Panel */}
      <SearchPanel onSearch={handleSearch} isLoading={isLoading} />

      {/* 2. Loading State with Railway Cold Start Calm Notice */}
      {isLoading && (
        <div className="flex flex-col gap-4">
          {showWakingUpMessage && (
            <div
              role="status"
              className="glass p-3.5 rounded-2xl border border-wheat/30 bg-wheat/5 text-wheat-ink text-xs font-medium flex items-center gap-2.5 animate-fadeIn"
            >
              <Clock className="w-4 h-4 shrink-0 text-wheat" />
              <span>{t("states.wakingUp")}</span>
            </div>
          )}
          <SkeletonResults />
        </div>
      )}

      {/* 3. Error State with Retry Button */}
      {!isLoading && errorMessage && (
        <div
          role="alert"
          className="glass p-6 rounded-2xl border border-clay/30 bg-clay/5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm"
        >
          <div className="flex items-center gap-3 text-sm text-ink">
            <AlertCircle className="w-5 h-5 text-clay shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button
            type="button"
            onClick={handleRetry}
            className="glass glass-pill px-4 py-2 text-xs font-semibold text-ink hover:text-forest flex items-center gap-2 cursor-pointer transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>{t("states.retry")}</span>
          </button>
        </div>
      )}

      {/* 4. Empty State */}
      {!isLoading && !errorMessage && resultsData && resultsData.results.length === 0 && (
        <div className="glass p-8 text-center text-sm text-ink-muted flex flex-col items-center justify-center gap-2">
          <p>{t("states.empty")}</p>
        </div>
      )}

      {/* 5. Results Area */}
      {!isLoading && !errorMessage && resultsData && resultsData.results.length > 0 && (
        <section aria-label={t("results.title")} className="flex flex-col gap-6 animate-fadeIn">
          {/* Warnings Strip */}
          <WarningsStrip warnings={resultsData.warnings} />

          {/* Headline Card */}
          <HeadlineCard data={resultsData} />

          {/* Results Comparison Table */}
          <ResultsTable results={resultsData.results} />

          {/* Cost Breakdown Stacked Bars */}
          <CostBreakdown results={resultsData.results} />

          {/* 7-Day Trend Chart */}
          <TrendChart
            mandiIds={mandiIds}
            bestMandiId={bestMandiId}
            commodity={commodity}
          />
        </section>
      )}
    </div>
  );
}
