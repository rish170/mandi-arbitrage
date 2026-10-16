"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "@/components/ThemeToggle";
import { LangToggle } from "@/components/LangToggle";
import { useI18n } from "@/lib/i18n";

export function Navbar() {
  const pathname = usePathname();
  const { t, lang } = useI18n();

  return (
    <header className="fixed top-4 left-0 right-0 z-50 flex justify-center px-4 pointer-events-none">
      <nav
        aria-label="Main Navigation"
        className="glass glass-pill pointer-events-auto w-full max-w-5xl px-5 py-2.5 flex items-center justify-between gap-4 shadow-sm"
      >
        {/* Wordmark in Fraunces */}
        <Link
          href="/"
          className="flex items-center gap-2 group cursor-pointer focus-visible:outline-none"
        >
          <span
            className={`text-lg sm:text-xl font-bold tracking-tight text-ink group-hover:text-forest transition-colors ${
              lang === "hi" ? "font-hindi-serif" : "font-display"
            }`}
          >
            {t("brand.name")}
          </span>
        </Link>

        {/* Navigation links & controls */}
        <div className="flex items-center gap-2 sm:gap-4">
          <div className="hidden sm:flex items-center gap-1 text-sm font-medium">
            <Link
              href="/"
              className={`px-3 py-1.5 rounded-full transition-colors ${
                pathname === "/"
                  ? "text-forest font-semibold"
                  : "text-ink-muted hover:text-ink"
              }`}
            >
              {t("nav.home")}
            </Link>
            <Link
              href="/methodology"
              className={`px-3 py-1.5 rounded-full transition-colors ${
                pathname === "/methodology"
                  ? "text-forest font-semibold"
                  : "text-ink-muted hover:text-ink"
              }`}
            >
              {t("nav.methodology")}
            </Link>
          </div>

          <div className="flex items-center gap-2">
            <LangToggle />
            <ThemeToggle />
          </div>
        </div>
      </nav>
    </header>
  );
}
