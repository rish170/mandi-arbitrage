/**
 * Indian currency and number formatting utilities following en-IN standard grouping.
 */

/**
 * Formats a value as Indian Rupee (₹) with Indian digit grouping (e.g., ₹12,34,567.89).
 */
export function formatCurrency(
  value: number | string | null | undefined,
  options: {
    showDecimals?: boolean;
    symbol?: string;
  } = {}
): string {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const num = typeof value === "number" ? value : parseFloat(String(value));
  if (isNaN(num)) {
    return "—";
  }

  const { showDecimals = true, symbol = "₹" } = options;

  const formattedNumber = new Intl.NumberFormat("en-IN", {
    minimumFractionDigits: showDecimals ? 2 : 0,
    maximumFractionDigits: showDecimals ? 2 : 0,
  }).format(num);

  return `${symbol}${formattedNumber}`;
}

/**
 * Formats a plain number with Indian digit grouping (e.g. 12,34,567).
 */
export function formatNumber(
  value: number | string | null | undefined,
  decimals: number = 0
): string {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const num = typeof value === "number" ? value : parseFloat(String(value));
  if (isNaN(num)) {
    return "—";
  }

  return new Intl.NumberFormat("en-IN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
}

/**
 * Formats a distance in kilometers with 1 decimal place.
 */
export function formatDistance(km: number | string | null | undefined): string {
  if (km === null || km === undefined || km === "") {
    return "—";
  }
  const num = typeof km === "number" ? km : parseFloat(String(km));
  if (isNaN(num)) return "—";
  return `${num.toFixed(1)} km`;
}
