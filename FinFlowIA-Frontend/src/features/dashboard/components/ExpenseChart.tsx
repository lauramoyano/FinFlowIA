import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/Card";
import { formatCurrency } from "@/shared/lib/utils";
import { getCategoryColor } from "@/features/dashboard/lib/category-colors";
import { useChartHighlight } from "@/features/dashboard/context/ChartHighlightContext";
import type { CategoryBreakdown } from "@/features/dashboard/api/dashboard.api";

interface ExpenseChartProps {
  data: CategoryBreakdown[];
}

export function ExpenseChart({ data }: ExpenseChartProps) {
  const { t, i18n } = useTranslation("dashboard");
  const { t: tTransactions } = useTranslation("transactions");
  const { toggleCategory, getOpacity } = useChartHighlight();

  const chartData = data
    .filter((cat) => parseFloat(cat.total) > 0)
    .map((cat) => ({
      category: cat.category,
      name: tTransactions(`categories.${cat.category}`),
      value: parseFloat(cat.total),
      percentage: cat.percentage,
    }))
    .sort((a, b) => b.value - a.value);

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t("charts.expenseBreakdown")}</CardTitle>
        </CardHeader>
        <CardContent className="flex h-48 items-center justify-center text-muted-foreground">
          {t("charts.noExpenseData")}
        </CardContent>
      </Card>
    );
  }

  // Horizontal bars read better than a pie once there are many categories
  // with long labels — each row stays legible instead of shrinking into a
  // sliver that's indistinguishable by color alone.
  const chartHeight = Math.max(280, chartData.length * 36);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("charts.expenseBreakdown")}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={chartHeight}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              type="number"
              className="text-xs"
              tickFormatter={(value: number) =>
                new Intl.NumberFormat(i18n.language === "en" ? "en-US" : "es-AR", {
                  notation: "compact",
                  compactDisplay: "short",
                }).format(value)
              }
            />
            <YAxis type="category" dataKey="name" className="text-xs" width={150} />
            <Tooltip
              formatter={(value: number) => [formatCurrency(value), t("charts.amount")]}
            />
            <Bar
              dataKey="value"
              radius={[0, 4, 4, 0]}
              onClick={(entry: { category: string }) => toggleCategory(entry.category)}
              className="cursor-pointer"
            >
              {chartData.map((entry) => (
                <Cell
                  key={entry.category}
                  fill={getCategoryColor(entry.category)}
                  fillOpacity={getOpacity(entry.category)}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
