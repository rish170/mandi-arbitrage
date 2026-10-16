"use client";

import React from "react";
import { useI18n } from "@/lib/i18n";

export default function Home() {
  const { t, lang } = useI18n();

  return (
    <div className="w-full flex flex-col gap-6 pt-4 sm:pt-8">
      {/* Tool-First Header: Compact, Left-Aligned, Serif */}
      <header className="flex flex-col gap-2 max-w-2xl text-left">
        <h1
          className={`text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-ink ${
            lang === "hi" ? "font-hindi-serif" : "font-display"
          }`}
        >
          {t("brand.name")}
        </h1>
        <p className="text-base sm:text-lg text-ink-muted leading-relaxed">
          {t("brand.tagline")}
        </p>
      </header>

      {/* Placeholder Search Panel Slot for Phase 6 */}
      <section
        aria-label="Search Panel Container"
        className="glass p-6 sm:p-8 mt-2 flex flex-col gap-4"
      >
        <div className="flex items-center justify-between border-b border-glass-border/40 pb-4">
          <h2 className="text-lg font-semibold text-ink">
            {t("search.submit")}
          </h2>
          <span className="glass glass-pill px-3 py-1 text-xs font-medium text-forest">
            Phase 5 Shell Active
          </span>
        </div>
        <p className="text-sm text-ink-muted">
          {lang === "hi"
            ? "मंडी खोज व शुद्ध लाभ गणना प्रपत्र चरण 6 में सक्रिय होगा।"
            : "Mandi locator and net profit comparison interface will be fully wired in Phase 6."}
        </p>
      </section>
    </div>
  );
}
