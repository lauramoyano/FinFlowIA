import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/Card";
import { CategoryBadge } from "@/features/transactions/components/CategoryBadge";
import { formatCurrency } from "@/shared/lib/utils";
import type { CategoryBreakdown } from "@/features/dashboard/api/dashboard.api";
import type { CategoryType } from "@/features/transactions/types/transaction.types";

interface CategoryBreakdownProps {
  categories: CategoryBreakdown[];
}

export function CategoryBreakdownList({ categories }: CategoryBreakdownProps) {
  const { t } = useTranslation("dashboard");
  const sorted = [...categories].sort(
    (a, b) => parseFloat(b.total) - parseFloat(a.total),
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("charts.categoryBreakdown")}</CardTitle>
      </CardHeader>
      <CardContent>
        {sorted.length === 0 ? (
          <p className="text-center text-muted-foreground py-8">{t("charts.noData")}</p>
        ) : (
          <div className="space-y-4 sm:space-y-3">
            {sorted.map((cat) => (
              <div key={cat.category} className="flex flex-col gap-1.5 sm:flex-row sm:items-center sm:gap-3">
                <div className="sm:w-44 sm:shrink-0">
                  <CategoryBadge category={cat.category as CategoryType} className="max-w-full truncate" />
                </div>
                <div className="flex-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">
                      {t("charts.transactionCount", { count: cat.count })}
                    </span>
                    <span className="font-medium">{formatCurrency(cat.total)}</span>
                  </div>
                  <div className="mt-1 flex items-center gap-2">
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{ width: `${Math.min(cat.percentage, 100)}%` }}
                      />
                    </div>
                    <span className="w-10 shrink-0 text-right text-xs text-muted-foreground">
                      {cat.percentage.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
