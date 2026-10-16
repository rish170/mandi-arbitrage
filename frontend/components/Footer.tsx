"use client";

import React from "react";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";

export function Footer() {
  const { t } = useI18n();

  return (
    <footer className="w-full border-t border-glass-border/40 py-10 px-4 mt-auto">
      <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6 text-xs text-ink-muted">
        {/* Attribution & disclaimer */}
        <div className="flex flex-col items-center md:items-start gap-1.5 text-center md:text-left">
          <p className="font-medium text-ink">
            {t("footer.dataSource")}
          </p>
          <p className="max-w-md">
            {t("footer.disclaimer")}
          </p>
        </div>

        {/* Links */}
        <div className="flex items-center gap-6">
          <Link
            href="/methodology"
            className="hover:text-forest transition-colors font-medium underline underline-offset-4"
          >
            {t("footer.methodology")}
          </Link>
          <a
            href="https://github.com/rish170/mandi-arbitrage/blob/main/docs/API.md"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-forest transition-colors font-medium underline underline-offset-4"
          >
            {t("footer.apiDocs")}
          </a>
        </div>
      </div>
    </footer>
  );
}
