"use client";

import React from "react";
import Link from "next/link";
import { ArrowLeft, BookOpen, ExternalLink, AlertTriangle, Layers, Calculator } from "lucide-react";
import { useI18n } from "@/lib/i18n";

export default function MethodologyPage() {
  const { t, lang } = useI18n();

  return (
    <div className="w-full flex flex-col gap-8 pt-2 sm:pt-6">
      {/* Back button */}
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-xs font-semibold text-ink-muted hover:text-forest transition-colors w-fit glass glass-pill px-3 py-1.5"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>{t("nav.home")}</span>
      </Link>

      {/* Header */}
      <header className="flex flex-col gap-2 max-w-3xl text-left">
        <h1
          className={`text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-ink ${
            lang === "hi" ? "font-hindi-serif" : "font-display"
          }`}
        >
          {t("methodology.title")}
        </h1>
        <p className="text-base sm:text-lg text-ink-muted leading-relaxed">
          {t("methodology.subtitle")}
        </p>
      </header>

      {/* 1. The Mathematical Formula */}
      <section aria-labelledby="formula-heading" className="glass p-6 sm:p-8 flex flex-col gap-5 shadow-sm">
        <div className="flex items-center gap-2.5 border-b border-glass-border/30 pb-3">
          <Calculator className="w-5 h-5 text-forest" />
          <h2 id="formula-heading" className="text-lg font-bold text-ink">
            {t("methodology.formulaTitle")}
          </h2>
        </div>

        <div className="flex flex-col gap-3 font-mono text-xs sm:text-sm bg-black/5 dark:bg-white/5 p-4 sm:p-5 rounded-2xl border border-glass-border/40 overflow-x-auto text-ink">
          <p className="font-semibold">{t("methodology.formulaStep1")}</p>
          <p className="text-clay">{t("methodology.formulaStep2")}</p>
          <p className="text-soil">{t("methodology.formulaStep3")}</p>
          <p className="font-bold text-forest text-sm sm:text-base pt-2 border-t border-glass-border/30">
            {t("methodology.formulaStep4")}
          </p>
        </div>
      </section>

      {/* 2. Worked Example */}
      <section aria-labelledby="example-heading" className="glass p-6 sm:p-8 flex flex-col gap-5 shadow-sm">
        <div className="flex items-center gap-2.5 border-b border-glass-border/30 pb-3">
          <BookOpen className="w-5 h-5 text-wheat" />
          <h2 id="example-heading" className="text-lg font-bold text-ink">
            Worked Example: 10 Quintals of Wheat at Nagpur APMC
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs sm:text-sm text-ink">
          <div className="glass-strong p-4 rounded-xl flex flex-col gap-2">
            <h3 className="font-bold text-ink">Input Parameters</h3>
            <ul className="space-y-1 text-ink-muted">
              <li><strong className="text-ink">Crop:</strong> Wheat (10.0 quintals)</li>
              <li><strong className="text-ink">Origin:</strong> 440001 (Nagpur City)</li>
              <li><strong className="text-ink">Destination:</strong> APMC Nagpur (Market Yard)</li>
              <li><strong className="text-ink">Road Distance:</strong> 2.9 km</li>
              <li><strong className="text-ink">Vehicle:</strong> Pickup (15 q capacity @ ₹18.0/km)</li>
              <li><strong className="text-ink">Quality Grade:</strong> Good (0% auction cut)</li>
            </ul>
          </div>

          <div className="glass-strong p-4 rounded-xl flex flex-col gap-2">
            <h3 className="font-bold text-ink">Calculated Realization</h3>
            <ul className="space-y-1 text-ink-muted">
              <li><strong className="text-ink">Modal Price:</strong> ₹2,900.00 / q</li>
              <li><strong className="text-ink">APMC Fee + Commission (3%):</strong> -₹87.00 / q</li>
              <li><strong className="text-ink">Vehicles Needed:</strong> ⌈10 / 15⌉ = 1 vehicle</li>
              <li><strong className="text-ink">Transport Cost:</strong> (1 × ₹18 × 2.9 km) / 10 = -₹5.22 / q</li>
              <li className="pt-2 border-t border-glass-border/30 font-bold text-forest text-sm">
                Net Profit: ₹2,807.78 / quintal (₹28,077.80 Total)
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* 3. Assumptions & Rates Table */}
      <section aria-labelledby="assumptions-heading" className="glass p-6 sm:p-8 flex flex-col gap-5 shadow-sm">
        <div className="flex items-center justify-between border-b border-glass-border/30 pb-3 flex-wrap gap-2">
          <div className="flex items-center gap-2.5">
            <Layers className="w-5 h-5 text-forest" />
            <h2 id="assumptions-heading" className="text-lg font-bold text-ink">
              {t("methodology.assumptionsTitle")}
            </h2>
          </div>
          <span className="glass glass-pill px-2.5 py-0.5 text-[11px] font-bold text-wheat-ink bg-wheat/10 border-wheat/30">
            STATUS: ASSUMPTION_UNVERIFIED
          </span>
        </div>

        <p className="text-xs sm:text-sm text-ink-muted">
          All baseline vehicle rates, mandi fees, and quality discount percentages are transparent assumptions. Farmers can edit fee %, commission %, and freight rates in the &quot;Advanced&quot; section of the search form.
        </p>

        <div className="overflow-x-auto rounded-xl border border-glass-border/40">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-black/5 dark:bg-white/5 border-b border-glass-border/40 text-ink-muted uppercase">
                <th className="py-2.5 px-3">Vehicle / Fee Category</th>
                <th className="py-2.5 px-3">Standard Capacity</th>
                <th className="py-2.5 px-3">Default Rate</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-glass-border/30 glass-strong">
              <tr>
                <td className="py-2 px-3 font-semibold text-ink">Tempo (Tata Ace / 3-wheeler)</td>
                <td className="py-2 px-3">8 quintals</td>
                <td className="py-2 px-3">₹14.0 / km</td>
                <td className="py-2 px-3 text-wheat-ink font-medium">Unverified Estimate</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-semibold text-ink">Bolero Pickup</td>
                <td className="py-2 px-3">15 quintals</td>
                <td className="py-2 px-3">₹18.0 / km</td>
                <td className="py-2 px-3 text-wheat-ink font-medium">Unverified Estimate</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-semibold text-ink">Mini Truck (Eicher 14ft/17ft)</td>
                <td className="py-2 px-3">40 quintals</td>
                <td className="py-2 px-3">₹26.0 / km</td>
                <td className="py-2 px-3 text-wheat-ink font-medium">Unverified Estimate</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-semibold text-ink">Truck (10/12 wheeler)</td>
                <td className="py-2 px-3">100 quintals</td>
                <td className="py-2 px-3">₹38.0 / km</td>
                <td className="py-2 px-3 text-wheat-ink font-medium">Unverified Estimate</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-semibold text-ink">Maharashtra APMC Market Fee</td>
                <td className="py-2 px-3">—</td>
                <td className="py-2 px-3">1.0% of realized value</td>
                <td className="py-2 px-3 text-forest font-medium">Statutory Default</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-semibold text-ink">Commission Agent Charge</td>
                <td className="py-2 px-3">—</td>
                <td className="py-2 px-3">2.0% of realized value</td>
                <td className="py-2 px-3 text-wheat-ink font-medium">Estimated Default</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* 4. Official Data Sources */}
      <section aria-labelledby="sources-heading" className="glass p-6 sm:p-8 flex flex-col gap-4 shadow-sm">
        <h2 id="sources-heading" className="text-lg font-bold text-ink border-b border-glass-border/30 pb-3">
          {t("methodology.sourcesTitle")}
        </h2>
        <ul className="space-y-3 text-xs sm:text-sm text-ink-muted">
          <li>
            <strong className="text-ink">data.gov.in Mandi Price Dataset:</strong> Daily wholesale arrivals and modal rates published by the Directorate of Marketing and Inspection (DMI), Ministry of Agriculture and Farmers Welfare. Updated twice daily.
          </li>
          <li>
            <strong className="text-ink">Google Routes API:</strong> Batched <code>computeRouteMatrix</code> driving distances between farm centroid and candidate mandi coordinates.
          </li>
          <li>
            <strong className="text-ink">OpenStreetMap Nominatim:</strong> Geocoding fallback engine when Google Geocoding quota is exceeded or unavailable.
          </li>
        </ul>
      </section>

      {/* 5. Practical Limitations */}
      <section aria-labelledby="limitations-heading" className="glass p-6 sm:p-8 flex flex-col gap-4 shadow-sm">
        <div className="flex items-center gap-2 border-b border-glass-border/30 pb-3 text-clay">
          <AlertTriangle className="w-5 h-5" />
          <h2 id="limitations-heading" className="text-lg font-bold text-ink">
            {t("methodology.limitationsTitle")}
          </h2>
        </div>
        <ul className="space-y-2 text-xs sm:text-sm text-ink-muted list-disc list-inside">
          <li><strong>Indicative Modal Prices:</strong> APMC published rates represent modal auction results from recent trading sessions. Spot prices fluctuate during active physical bidding.</li>
          <li><strong>Lot Quality Variations:</strong> Moisture levels, foreign matter, and grain size are evaluated by physical inspection at the auction platform.</li>
          <li><strong>Road Distance Fallback:</strong> If routing APIs are unavailable, distances use straight-line haversine multiplied by a 1.3 highway geometry factor.</li>
          <li><strong>Historical Trends:</strong> Trend lines use seeded demo history until 7 consecutive days of live snapshots are ingested into our database.</li>
        </ul>
      </section>

      {/* 6. Documentation & OpenAPI Links */}
      <section className="glass p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-bold text-ink">Developer API &amp; Specifications</h3>
          <p className="text-xs text-ink-muted">Inspect schema contracts and integration endpoints.</p>
        </div>
        <div className="flex items-center gap-3">
          <a
            href="https://github.com/rish170/mandi-arbitrage/blob/main/docs/API.md"
            target="_blank"
            rel="noopener noreferrer"
            className="glass glass-pill px-4 py-2 text-xs font-semibold text-ink hover:text-forest flex items-center gap-1.5 transition-colors"
          >
            <span>API Guide</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
          <a
            href="https://github.com/rish170/mandi-arbitrage/blob/main/docs/openapi.json"
            target="_blank"
            rel="noopener noreferrer"
            className="glass glass-pill px-4 py-2 text-xs font-semibold text-ink hover:text-forest flex items-center gap-1.5 transition-colors"
          >
            <span>OpenAPI JSON</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </section>
    </div>
  );
}
