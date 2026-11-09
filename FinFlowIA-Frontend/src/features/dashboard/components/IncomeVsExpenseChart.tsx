import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/Card";
import { formatCurrency } from "@/shared/lib/utils";
import { EXPENSE_COLOR, INCOME_COLOR } from "@/features/dashboard/lib/category-colors";
import type { TimeSeriesPoint } from "@/features/dashboard/api/dashboard.api";

interface IncomeVsExpenseChartProps {
  timeSeries: TimeSeriesPoint[];
}

export function IncomeVsExpenseChart({ timeSeries }: IncomeVsExpenseChartProps) {
  const { t, i18n } = useTranslation("dashboard");

  const chartData = timeSeries.map((p) => ({
    period: p.period,
    income: parseFloat(p.income),
    expense: parseFloat(p.expense),
  }));

  const hasData = chartData.some((p) => p.income > 0 || p.expense > 0);

  if (!hasData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t("charts.incomeVsExpense")}</CardTitle>
        </CardHeader>
        <CardContent className="flex h-48 items-center justify-center text-muted-foreground">
          {t("charts.noChartData")}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("charts.incomeVsExpense")}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis dataKey="period" className="text-xs" />
            <YAxis
              className="text-xs"
              tickFormatter={(value: number) =>
                new Intl.NumberFormat(i18n.language === "en" ? "en-US" : "es-AR", {
                  notation: "compact",
                  compactDisplay: "short",
                }).format(value)
              }
            />
            <Tooltip formatter={(value: number, name: string) => [formatCurrency(value), name]} />
            <Legend />
            <Bar dataKey="income" name={t("charts.income")} fill={INCOME_COLOR} radius={[4, 4, 0, 0]} />
            <Bar dataKey="expense" name={t("charts.expense")} fill={EXPENSE_COLOR} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
