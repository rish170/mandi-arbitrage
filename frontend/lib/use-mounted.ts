"use client";

import { useSyncExternalStore } from "react";

const emptySubscribe = () => () => {};

/**
 * Hook to safely detect client-side mounting without triggering cascading renders or hydration mismatch.
 * Returns false on the server / initial hydration and true on the client.
 */
export function useMounted(): boolean {
  return useSyncExternalStore(
    emptySubscribe,
    () => true,
    () => false
  );
}
