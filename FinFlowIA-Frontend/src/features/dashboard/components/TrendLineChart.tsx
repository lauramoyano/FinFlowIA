import {
  CartesianGrid,
  Line,
  LineChart,
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

interface TrendLineChartProps {
  timeSeries: TimeSeriesPoint[];
}

export function TrendLineChart({ timeSeries }: TrendLineChartProps) {
  const { t, i18n } = useTranslation("dashboard");

  const chartData = timeSeries.map((p) => ({
    period: p.period,
    balance: parseFloat(p.income) - parseFloat(p.expense),
  }));

  const hasData = chartData.some((p) => p.balance !== 0);
  const endsPositive = chartData.length > 0 && chartData[chartData.length - 1].balance >= 0;
  const lineColor = endsPositive ? INCOME_COLOR : EXPENSE_COLOR;

  if (!hasData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t("charts.trend")}</CardTitle>
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
        <CardTitle>{t("charts.trend")}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={chartData} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
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
            <Tooltip formatter={(value: number) => [formatCurrency(value), t("summary.netBalance")]} />
            <Line type="monotone" dataKey="balance" stroke={lineColor} strokeWidth={2} dot />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
