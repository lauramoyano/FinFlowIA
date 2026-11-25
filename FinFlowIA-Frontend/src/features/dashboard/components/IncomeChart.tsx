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
import { INCOME_COLOR } from "@/features/dashboard/lib/category-colors";
import { useChartHighlight } from "@/features/dashboard/context/ChartHighlightContext";
import type { CategoryBreakdown } from "@/features/dashboard/api/dashboard.api";

interface IncomeChartProps {
  incomeCategories: CategoryBreakdown[];
}

export function IncomeChart({ incomeCategories }: IncomeChartProps) {
  const { t, i18n } = useTranslation("dashboard");
  const { t: tTransactions } = useTranslation("transactions");
  const { toggleCategory, getOpacity } = useChartHighlight();

  const chartData = incomeCategories
    .filter((cat) => parseFloat(cat.total) > 0)
    .map((cat) => ({
      category: cat.category,
      name: tTransactions(`categories.${cat.category}`),
      amount: parseFloat(cat.total),
    }));

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t("charts.incomeSources")}</CardTitle>
        </CardHeader>
        <CardContent className="flex h-48 items-center justify-center text-muted-foreground">
          {t("charts.noIncomeData")}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("charts.incomeSources")}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis dataKey="name" className="text-xs" />
            <YAxis
              className="text-xs"
              tickFormatter={(value: number) =>
                new Intl.NumberFormat(i18n.language === "en" ? "en-US" : "es-AR", {
                  notation: "compact",
                  compactDisplay: "short",
                }).format(value)
              }
            />
            <Tooltip formatter={(value: number) => [formatCurrency(value), t("charts.amount")]} />
            <Bar
              dataKey="amount"
              radius={[4, 4, 0, 0]}
              onClick={(data: { category: string }) => toggleCategory(data.category)}
              className="cursor-pointer"
            >
              {chartData.map((entry) => (
                <Cell
                  key={entry.category}
                  fill={INCOME_COLOR}
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
