import type { TFunction } from "i18next";

/** The 11 system default categories that have a translation key in transactions.json. */
export const DEFAULT_CATEGORY_NAMES = new Set([
  "food", "transport", "utilities", "supplies", "marketing",
  "payroll", "rent", "equipment", "sales", "services", "other", "uncategorized",
]);

/**
 * Resolve a display label for a category name: translated for the fixed
 * defaults, capitalized as-is for user-created custom categories (which
 * have no translation key — they're free text the user typed).
 */
export function getCategoryLabel(t: TFunction<"transactions">, name: string): string {
  if (DEFAULT_CATEGORY_NAMES.has(name)) {
    return t(`categories.${name}`);
  }
  return name.charAt(0).toUpperCase() + name.slice(1);
}
