"use client";

import * as React from "react";
import { useTheme } from "next-themes";
import { Sun, Moon } from "lucide-react";
import { useMounted } from "@/lib/use-mounted";

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const mounted = useMounted();

  if (!mounted) {
    return (
      <button
        type="button"
        className="glass glass-pill p-2 w-9 h-9 flex items-center justify-center text-ink opacity-70 cursor-default"
        aria-label="Toggle theme"
      >
        <span className="w-4 h-4 block" />
      </button>
    );
  }

  const isDark = resolvedTheme === "dark";
  const ariaLabel = isDark ? "Switch to light mode" : "Switch to dark mode";

  const toggleTheme = () => {
    setTheme(isDark ? "light" : "dark");
  };

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="glass glass-pill p-2 w-9 h-9 flex items-center justify-center text-ink hover:text-forest active:scale-95 transition-all duration-200 cursor-pointer"
      aria-label={ariaLabel}
      title={ariaLabel}
    >
      <div className="relative w-4 h-4 flex items-center justify-center">
        {isDark ? (
          <Sun
            className="w-4 h-4 text-wheat transition-transform duration-200 ease-in-out rotate-0 scale-100"
            aria-hidden="true"
          />
        ) : (
          <Moon
            className="w-4 h-4 text-forest transition-transform duration-200 ease-in-out rotate-0 scale-100"
            aria-hidden="true"
          />
        )}
      </div>
    </button>
  );
}
