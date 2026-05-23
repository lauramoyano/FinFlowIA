import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/Card";
import { LoadingSpinner } from "@/shared/components/LoadingSpinner";
import { CategoryBadge } from "@/features/transactions/components/CategoryBadge";
import { formatCurrency, formatDate } from "@/shared/lib/utils";
import type { ReportData } from "@/features/reports/api/reports.api";
import type { CategoryType } from "@/features/transactions/types/transaction.types";

interface ReportPreviewProps {
  report: ReportData | undefined;
  isLoading: boolean;
}

export function ReportPreview({ report, isLoading }: ReportPreviewProps) {
  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex h-64 flex-col items-center justify-center text-muted-foreground">
        <p>Select a date range and click Generate to see your report</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Total Income</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-green-600">
              {formatCurrency(report.total_income)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Total Expenses</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-red-600">
              {formatCurrency(report.total_expenses)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Net Balance</CardTitle>
          </CardHeader>
          <CardContent>
            <p className={`text-2xl font-bold ${parseFloat(report.net_balance) >= 0 ? "text-green-600" : "text-red-600"}`}>
              {formatCurrency(report.net_balance)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Category Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>
            Category Breakdown — {formatDate(report.start_date)} to {formatDate(report.end_date)}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="pb-2 text-left font-medium text-muted-foreground">Category</th>
                <th className="pb-2 text-right font-medium text-muted-foreground">Transactions</th>
                <th className="pb-2 text-right font-medium text-muted-foreground">Total</th>
                <th className="pb-2 text-right font-medium text-muted-foreground">Share</th>
              </tr>
            </thead>
            <tbody>
              {report.by_category.map((cat) => (
                <tr key={cat.category} className="border-b last:border-0">
                  <td className="py-2">
                    <CategoryBadge category={cat.category as CategoryType} />
                  </td>
                  <td className="py-2 text-right text-muted-foreground">{cat.count}</td>
                  <td className="py-2 text-right font-medium">{formatCurrency(cat.total)}</td>
                  <td className="py-2 text-right text-muted-foreground">{cat.percentage.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground text-right">
        Generated at {new Date(report.generated_at).toLocaleString()}
      </p>
    </div>
  );
}
