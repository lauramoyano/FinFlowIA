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
import { EXPENSE_COLOR, INCOME_COLOR } from "@/features/dashboard/lib/category-colors";
import { useChartHighlight } from "@/features/dashboard/context/ChartHighlightContext";
import type { CategoryBreakdown } from "@/features/dashboard/api/dashboard.api";

interface WaterfallStep {
  name: string;
  category: string | null; // null for the non-toggleable Income/Balance totals
  base: number;
  value: number;
  isTotal: boolean;
  isPositive: boolean; // controls color for the Income/Balance total bars
}

function buildWaterfallData(
  byCategory: CategoryBreakdown[],
  labelFor: (category: string) => string,
  incomeLabel: string,
  balanceLabel: string,
): WaterfallStep[] {
  const income = byCategory.filter((c) => c.transaction_type === "income");
  const expenses = [...byCategory]
    .filter((c) => c.transaction_type === "expense")
    .sort((a, b) => parseFloat(b.total) - parseFloat(a.total));

  const totalIncome = income.reduce((sum, c) => sum + parseFloat(c.total), 0);

  const steps: WaterfallStep[] = [
    { name: incomeLabel, category: null, base: 0, value: totalIncome, isTotal: true, isPositive: true },
  ];

  let running = totalIncome;
  for (const cat of expenses) {
    const amount = parseFloat(cat.total);
    steps.push({
      name: labelFor(cat.category),
      category: cat.category,
      base: running - amount,
      value: amount,
      isTotal: false,
      isPositive: false,
    });
    running -= amount;
  }

  steps.push({
    name: balanceLabel,
    category: null,
    base: 0,
    value: running,
    isTotal: true,
    isPositive: running >= 0,
  });
  return steps;
}

interface WaterfallChartProps {
  byCategory: CategoryBreakdown[];
}

export function WaterfallChart({ byCategory }: WaterfallChartProps) {
  const { t } = useTranslation("dashboard");
  const { t: tTransactions } = useTranslation("transactions");
  const { toggleCategory, getOpacity } = useChartHighlight();

  const chartData = buildWaterfallData(
    byCategory,
    (category) => tTransactions(`categories.${category}`),
    t("charts.waterfallIncome"),
    t("charts.waterfallBalance"),
  );

  const hasData = byCategory.length > 0;

  if (!hasData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t("charts.waterfall")}</CardTitle>
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
        <CardTitle>{t("charts.waterfall")}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} margin={{ top: 5, right: 20, left: 20, bottom: 35 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="name"
              className="text-xs"
              interval={0}
              angle={-35}
              textAnchor="end"
              height={60}
            />
            <YAxis
              className="text-xs"
              tickFormatter={(value: number) =>
                new Intl.NumberFormat("es-AR", { notation: "compact", compactDisplay: "short" }).format(
                  value,
                )
              }
            />
            <Tooltip
              formatter={(value: number) => [formatCurrency(value), t("charts.amount")]}
            />
            <Bar dataKey="base" stackId="waterfall" fill="transparent" />
            <Bar
              dataKey="value"
              stackId="waterfall"
              radius={[4, 4, 0, 0]}
              onClick={(entry: WaterfallStep) => entry.category && toggleCategory(entry.category)}
              className="cursor-pointer"
            >
              {chartData.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={entry.isPositive ? INCOME_COLOR : EXPENSE_COLOR}
                  fillOpacity={entry.category ? getOpacity(entry.category) : 1}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
