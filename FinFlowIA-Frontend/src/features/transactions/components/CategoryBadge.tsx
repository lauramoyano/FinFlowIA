import { cn } from "@/shared/lib/utils";
import type { CategoryType } from "@/features/transactions/types/transaction.types";

const CATEGORY_CONFIG: Record<
  CategoryType,
  { label: string; className: string }
> = {
  food: { label: "Food", className: "bg-orange-100 text-orange-700" },
  transport: { label: "Transport", className: "bg-blue-100 text-blue-700" },
  utilities: { label: "Utilities", className: "bg-yellow-100 text-yellow-700" },
  supplies: { label: "Supplies", className: "bg-purple-100 text-purple-700" },
  marketing: { label: "Marketing", className: "bg-pink-100 text-pink-700" },
  payroll: { label: "Payroll", className: "bg-red-100 text-red-700" },
  rent: { label: "Rent", className: "bg-indigo-100 text-indigo-700" },
  equipment: { label: "Equipment", className: "bg-cyan-100 text-cyan-700" },
  sales: { label: "Sales", className: "bg-green-100 text-green-700" },
  services: { label: "Services", className: "bg-teal-100 text-teal-700" },
  other: { label: "Other", className: "bg-gray-100 text-gray-700" },
  uncategorized: { label: "Uncategorized", className: "bg-gray-50 text-gray-500" },
};

interface CategoryBadgeProps {
  category: CategoryType | null;
  className?: string;
}

export function CategoryBadge({ category, className }: CategoryBadgeProps) {
  const cat = category ?? "uncategorized";
  const config = CATEGORY_CONFIG[cat] ?? CATEGORY_CONFIG.other;

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        config.className,
        className,
      )}
    >
      {config.label}
    </span>
  );
}
