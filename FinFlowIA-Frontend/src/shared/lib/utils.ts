import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind CSS classes with conflict resolution.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format a monetary amount for display.
 * Supports ARS (Argentine Peso) and USD.
 */
export function formatCurrency(
  amount: number | string,
  currency: "ARS" | "USD" = "ARS",
): string {
  const num = typeof amount === "string" ? parseFloat(amount) : amount;

  if (isNaN(num)) return "-";

  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
}

/**
 * Format a date string or Date object for display.
 */
export function formatDate(
  date: string | Date,
  locale: string = "es-AR",
): string {
  const d = typeof date === "string" ? new Date(date + "T00:00:00") : date;
  return d.toLocaleDateString(locale, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/**
 * Truncate a string to a maximum length with an ellipsis.
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength) + "…";
}
