"use client";

import React from "react";
import { useI18n } from "@/lib/i18n";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function MethodologyPage() {
  const { t, lang } = useI18n();

  return (
    <div className="w-full flex flex-col gap-6 pt-4 sm:pt-8">
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-sm text-ink-muted hover:text-forest transition-colors w-fit"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>{t("nav.home")}</span>
      </Link>

      <header className="flex flex-col gap-2 max-w-2xl text-left">
        <h1
          className={`text-3xl sm:text-4xl font-bold tracking-tight text-ink ${
            lang === "hi" ? "font-hindi-serif" : "font-display"
          }`}
        >
          {t("nav.methodology")}
        </h1>
        <p className="text-base text-ink-muted leading-relaxed">
          {lang === "hi"
            ? "शुद्ध मुनाफा गणना का पारदर्शी गणितीय सूत्र एवं डेटा नियम।"
            : "Mathematical formulation and data principles behind net profit realization."}
        </p>
      </header>

      <section className="glass p-6 sm:p-8 flex flex-col gap-4 text-sm text-ink">
        <h2 className="text-lg font-semibold text-ink border-b border-glass-border/40 pb-2">
          {lang === "hi" ? "शुद्ध लाभ सूत्र" : "Net Profit Realization Formula"}
        </h2>
        <div className="font-mono text-xs bg-bg/40 p-4 rounded-xl border border-glass-border/60 overflow-x-auto space-y-1">
          <p>Realized = Modal Price × (1 - Quality Cut % / 100)</p>
          <p>APMC Fees = Realized × (Market Fee % + Commission %) / 100</p>
          <p>Vehicles = ⌈Quantity / Vehicle Capacity⌉</p>
          <p>Transport / q = (Vehicles × Rate/km × Road km) / Quantity</p>
          <p className="text-forest font-bold pt-2">
            Net Realization / q = Realized - APMC Fees - Transport / q - Other Charges
          </p>
        </div>
      </section>
    </div>
  );
}
