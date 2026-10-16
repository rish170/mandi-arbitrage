"use client";

import React from "react";
import { useI18n } from "@/lib/i18n";
import { useMounted } from "@/lib/use-mounted";

export function LangToggle() {
  const { lang, setLang } = useI18n();
  const mounted = useMounted();

  if (!mounted) {
    return (
      <div className="glass glass-pill px-3 py-1.5 h-9 flex items-center justify-center text-xs font-semibold tracking-wide text-ink opacity-70">
        <span>EN</span>
        <span className="mx-1.5 opacity-40">|</span>
        <span>हिं</span>
      </div>
    );
  }

  return (
    <div
      role="group"
      aria-label="Language selection"
      className="glass glass-pill px-2.5 py-1 h-9 flex items-center justify-center text-xs font-semibold tracking-wide"
    >
      <button
        type="button"
        onClick={() => setLang("en")}
        className={`px-1.5 py-0.5 rounded-full transition-colors duration-200 cursor-pointer ${
          lang === "en"
            ? "text-forest font-bold"
            : "text-ink-muted hover:text-ink"
        }`}
        aria-pressed={lang === "en"}
        aria-label="Switch to English"
      >
        EN
      </button>
      <span className="text-ink-muted opacity-40 select-none" aria-hidden="true">
        |
      </span>
      <button
        type="button"
        onClick={() => setLang("hi")}
        className={`px-1.5 py-0.5 rounded-full transition-colors duration-200 cursor-pointer font-hindi ${
          lang === "hi"
            ? "text-forest font-bold"
            : "text-ink-muted hover:text-ink"
        }`}
        aria-pressed={lang === "hi"}
        aria-label="हिंदी में बदलें"
      >
        हिं
      </button>
    </div>
  );
}
