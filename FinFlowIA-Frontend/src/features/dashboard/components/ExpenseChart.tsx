import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/Card";
import { formatCurrency } from "@/shared/lib/utils";
import type { CategoryBreakdown } from "@/features/dashboard/api/dashboard.api";

const COLORS = [
  "#8A05BE", "#10b981", "#f59e0b", "#ef4444", "#3b82f6",
  "#06b6d4", "#f97316", "#84cc16", "#ec4899", "#6366f1",
];

interface ExpenseChartProps {
  data: CategoryBreakdown[];
}

export function ExpenseChart({ data }: ExpenseChartProps) {
  const { t } = useTranslation("dashboard");
  const { t: tTransactions } = useTranslation("transactions");

  const chartData = data
    .filter((cat) => parseFloat(cat.total) > 0)
    .map((cat) => ({
      name: tTransactions(`categories.${cat.category}`),
      value: parseFloat(cat.total),
      percentage: cat.percentage,
    }));

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

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("charts.expenseBreakdown")}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={2}
              dataKey="value"
            >
              {chartData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number) => [formatCurrency(value), t("charts.amount")]}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
