import { useTranslation } from "react-i18next";
import { cn } from "@/shared/lib/utils";
import { getCategoryLabel } from "@/features/transactions/lib/category-label";
import type { CategoryType } from "@/features/transactions/types/transaction.types";

// Record<string, string>, not Record<CategoryType, string>: CategoryType
// includes an open `string` branch (custom categories), so a finite object
// literal can't satisfy it as an index type. Custom categories fall back to
// the "other" styling below.
//
// A single purple/violet/fuchsia family at varying shades — matching the
// monochrome purple ramp used for charts (features/dashboard/lib/category-colors.ts)
// — instead of a rainbow of unrelated hues, so a pill reads as part of the
// same app as the rest of the (grayscale + one purple accent) UI. The label
// text is always shown alongside, so a shared hue family is never the sole
// identifier between categories.
const CATEGORY_CLASSNAMES: Record<string, string> = {
  payroll: "bg-violet-200 text-violet-900 dark:bg-violet-900/50 dark:text-violet-200",
  sales: "bg-violet-100 text-violet-800 dark:bg-violet-900/40 dark:text-violet-300",
  services: "bg-purple-200 text-purple-900 dark:bg-purple-900/50 dark:text-purple-200",
  rent: "bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300",
  utilities: "bg-fuchsia-100 text-fuchsia-800 dark:bg-fuchsia-900/40 dark:text-fuchsia-300",
  marketing: "bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300",
  equipment: "bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300",
  food: "bg-fuchsia-50 text-fuchsia-700 dark:bg-fuchsia-900/30 dark:text-fuchsia-300",
  transport: "bg-violet-50 text-violet-600 dark:bg-violet-900/20 dark:text-violet-300",
  supplies: "bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-300",
  other: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  uncategorized: "bg-gray-50 text-gray-500 dark:bg-gray-800/60 dark:text-gray-400",
};

interface CategoryBadgeProps {
  category: CategoryType | null;
  className?: string;
}

export function CategoryBadge({ category, className }: CategoryBadgeProps) {
  const { t } = useTranslation("transactions");
  const cat = category ?? "uncategorized";
  const badgeClassName = CATEGORY_CLASSNAMES[cat] ?? CATEGORY_CLASSNAMES.other;

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        badgeClassName,
        className,
      )}
    >
      {getCategoryLabel(t, cat)}
    </span>
  );
}
