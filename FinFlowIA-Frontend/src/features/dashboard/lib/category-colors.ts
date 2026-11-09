// Fixed step per category name, assigned once — never by array index of a
// given render's filtered/sorted dataset, so a category keeps its color
// across re-renders, filters, and chart types.
//
// Used only by the expense breakdown chart (ExpenseChart). A single-hue RED
// ramp — not a multi-hue categorical set — because this app colors expenses
// red / income green everywhere else (SummaryCards, IncomeChart,
// IncomeVsExpenseChart, CombinedChart, TrendLineChart, WaterfallChart); an
// expense-only chart's per-category steps are shades of that same red
// rather than an unrelated hue family. Defined as CSS custom properties in
// index.css (--chart-*) with separate light/dark steps, so theme switching
// needs no JS — same pattern as --primary etc.
//
// Trade-off, deliberate: a monochrome ramp used for identity (not magnitude)
// fails the categorical CVD-adjacency check by design (validated via the
// dataviz skill's validate_palette.js — lightness band, chroma floor, and
// contrast all pass; CVD separation does not, since adjacent steps share a
// hue). Every chart that uses this always shows the category name directly
// (axis label, legend, or tooltip), so color is a supporting cue, never the
// sole identifier.
const CATEGORY_COLOR_VAR: Record<string, string> = {
  payroll: "--chart-payroll",
  rent: "--chart-rent",
  utilities: "--chart-utilities",
  marketing: "--chart-marketing",
  equipment: "--chart-equipment",
  food: "--chart-food",
  sales: "--chart-sales",
  services: "--chart-services",
  transport: "--chart-transport",
  supplies: "--chart-supplies",
  other: "--chart-neutral",
  uncategorized: "--chart-neutral-muted",
};

const FALLBACK_VARS = Object.values(CATEGORY_COLOR_VAR).slice(0, 10);

/** Stable color for a category name — custom (non-default) names hash into the same ramp. */
export function getCategoryColor(category: string): string {
  const cssVar = CATEGORY_COLOR_VAR[category] ?? FALLBACK_VARS[hashCategory(category) % FALLBACK_VARS.length];
  return `hsl(var(${cssVar}))`;
}

function hashCategory(category: string): number {
  let hash = 0;
  for (let i = 0; i < category.length; i++) {
    hash = (hash * 31 + category.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

// Theme-aware: a slightly darker emerald in light mode, the original shade
// kept for dark — see --chart-income in index.css.
export const INCOME_COLOR = "hsl(var(--chart-income))";
// Theme-aware: darker red in light mode (matches the expense ramp's "Nómina"
// step), lighter red in dark mode — see --chart-expense in index.css.
export const EXPENSE_COLOR = "hsl(var(--chart-expense))";
