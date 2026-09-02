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
          <div className="space-y-3">
            {sorted.map((cat) => (
              <div key={cat.category} className="flex items-center gap-3">
                <CategoryBadge category={cat.category as CategoryType} />
                <div className="flex-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">
                      {t("charts.transactionCount", { count: cat.count })}
                    </span>
                    <span className="font-medium">{formatCurrency(cat.total)}</span>
                  </div>
                  <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary"
                      style={{ width: `${Math.min(cat.percentage, 100)}%` }}
                    />
                  </div>
                </div>
                <span className="w-12 text-right text-xs text-muted-foreground">
                  {cat.percentage.toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
