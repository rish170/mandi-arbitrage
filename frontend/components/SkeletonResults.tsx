"use client";

import React from "react";

export function SkeletonResults() {
  return (
    <div
      role="status"
      aria-label="Loading comparison results"
      className="w-full flex flex-col gap-6 animate-pulse"
    >
      {/* HeadlineCard Skeleton */}
      <div className="glass p-6 sm:p-7 flex flex-col gap-3 border-l-4 border-l-wheat/40">
        <div className="h-4 w-24 bg-ink/10 dark:bg-white/10 rounded-full" />
        <div className="h-6 w-3/4 bg-ink/10 dark:bg-white/10 rounded-lg" />
        <div className="h-4 w-1/2 bg-ink/10 dark:bg-white/10 rounded-lg" />
      </div>

      {/* Table Skeleton */}
      <div className="glass p-5 flex flex-col gap-3">
        <div className="h-8 w-full bg-ink/10 dark:bg-white/10 rounded-xl" />
        <div className="h-12 w-full bg-ink/5 dark:bg-white/5 rounded-xl" />
        <div className="h-12 w-full bg-ink/5 dark:bg-white/5 rounded-xl" />
        <div className="h-12 w-full bg-ink/5 dark:bg-white/5 rounded-xl" />
        <div className="h-12 w-full bg-ink/5 dark:bg-white/5 rounded-xl" />
      </div>

      {/* Cost Breakdown Skeleton */}
      <div className="glass p-5 flex flex-col gap-3">
        <div className="h-5 w-40 bg-ink/10 dark:bg-white/10 rounded-lg" />
        <div className="h-6 w-full bg-ink/10 dark:bg-white/10 rounded-full" />
        <div className="h-6 w-full bg-ink/10 dark:bg-white/10 rounded-full" />
      </div>
    </div>
  );
}
