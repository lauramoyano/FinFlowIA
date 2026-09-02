import { useTranslation } from "react-i18next";
import { cn } from "@/shared/lib/utils";
import { getCategoryLabel } from "@/features/transactions/lib/category-label";
import type { CategoryType } from "@/features/transactions/types/transaction.types";

// Record<string, string>, not Record<CategoryType, string>: CategoryType
// includes an open `string` branch (custom categories), so a finite object
// literal can't satisfy it as an index type. Custom categories fall back to
// the "other" styling below.
const CATEGORY_CLASSNAMES: Record<string, string> = {
  food: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300",
  transport: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
  utilities: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300",
  supplies: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300",
  marketing: "bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300",
  payroll: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
  rent: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300",
  equipment: "bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300",
  sales: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300",
  services: "bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300",
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
