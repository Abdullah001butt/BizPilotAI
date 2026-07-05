/**
 * Money is stored and transmitted as integer minor units (cents). These helpers
 * convert between cents and the major-unit values shown/entered in the UI.
 */

/** Format cents as a currency string, e.g. 3150 → "$31.50". */
export function formatMoney(cents: number, currency = "USD"): string {
  try {
    return new Intl.NumberFormat(undefined, { style: "currency", currency }).format(
      cents / 100,
    );
  } catch {
    return `${(cents / 100).toFixed(2)} ${currency}`;
  }
}

/** Convert a major-unit input (e.g. "31.50") to integer cents. */
export function toCents(major: number | string): number {
  const value = typeof major === "string" ? Number.parseFloat(major) : major;
  if (Number.isNaN(value)) return 0;
  return Math.round(value * 100);
}

/** Convert integer cents to a major-unit number (for form fields). */
export function toMajor(cents: number): number {
  return cents / 100;
}
