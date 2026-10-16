"use client";

import React from "react";
import { AlertTriangle } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { WarningItem } from "@/lib/api";

interface WarningsStripProps {
  warnings: WarningItem[];
}

export function WarningsStrip({ warnings }: WarningsStripProps) {
  const { t } = useI18n();

  if (!warnings || warnings.length === 0) return null;

  return (
    <div
      role="alert"
      aria-label="Notices and Data Warnings"
      className="glass p-4 rounded-2xl border-l-4 border-l-clay border-clay/30 bg-clay/5 flex flex-col gap-2 shadow-sm"
    >
      <div className="flex items-center gap-2 text-clay font-bold text-xs uppercase tracking-wider">
        <AlertTriangle className="w-4 h-4 text-clay" />
        <span>Notice</span>
      </div>

      <ul className="flex flex-col gap-1 text-xs text-ink list-disc list-inside">
        {warnings.map((w, idx) => {
          const translatedMessage = t(`warnings.${w.code}`, w.message);
          return (
            <li key={idx} className="leading-relaxed">
              <span className="font-semibold text-ink-muted">[{w.code}]:</span>{" "}
              {translatedMessage}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
