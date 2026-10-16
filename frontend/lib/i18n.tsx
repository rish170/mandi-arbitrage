"use client";

import React, {
  createContext,
  useContext,
  useCallback,
  useSyncExternalStore,
} from "react";
import enTranslations from "@/locales/en.json";
import hiTranslations from "@/locales/hi.json";

export type Language = "en" | "hi";

type TranslationRecord = Record<string, unknown>;

const translations: Record<Language, TranslationRecord> = {
  en: enTranslations as TranslationRecord,
  hi: hiTranslations as TranslationRecord,
};

interface I18nContextType {
  lang: Language;
  setLang: (lang: Language) => void;
  t: (path: string, fallback?: string) => string;
}

const I18nContext = createContext<I18nContextType | null>(null);

const STORAGE_KEY = "mandi_lang";
const LANG_CHANGE_EVENT = "mandi_lang_change";

function getLangSnapshot(): Language {
  if (typeof window === "undefined") return "en";
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved === "hi" ? "hi" : "en";
  } catch {
    return "en";
  }
}

function getLangServerSnapshot(): Language {
  return "en";
}

function subscribe(callback: () => void) {
  if (typeof window === "undefined") return () => {};
  window.addEventListener(LANG_CHANGE_EVENT, callback);
  window.addEventListener("storage", callback);
  return () => {
    window.removeEventListener(LANG_CHANGE_EVENT, callback);
    window.removeEventListener("storage", callback);
  };
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const lang = useSyncExternalStore(
    subscribe,
    getLangSnapshot,
    getLangServerSnapshot
  );

  const setLang = useCallback((newLang: Language) => {
    try {
      localStorage.setItem(STORAGE_KEY, newLang);
      document.documentElement.lang = newLang;
      window.dispatchEvent(new Event(LANG_CHANGE_EVENT));
    } catch {
      // ignore
    }
  }, []);

  const t = useCallback(
    (path: string, fallback?: string): string => {
      const keys = path.split(".");

      const lookup = (dict: TranslationRecord): string | null => {
        let current: unknown = dict;
        for (const k of keys) {
          if (
            current &&
            typeof current === "object" &&
            k in (current as Record<string, unknown>)
          ) {
            current = (current as Record<string, unknown>)[k];
          } else {
            return null;
          }
        }
        return typeof current === "string" ? current : null;
      };

      const resolved = lookup(translations[lang]);
      if (resolved !== null) return resolved;

      // Fallback to English
      const enResolved = lookup(translations.en);
      if (enResolved !== null) return enResolved;

      return fallback || path;
    },
    [lang]
  );

  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    throw new Error("useI18n must be used within an I18nProvider");
  }
  return ctx;
}
