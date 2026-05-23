import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/Card";
import { formatCurrency } from "@/shared/lib/utils";
import type { CategoryBreakdown } from "@/features/dashboard/api/dashboard.api";

const COLORS = [
  "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
  "#06b6d4", "#f97316", "#84cc16", "#ec4899", "#6366f1",
];

interface ExpenseChartProps {
  data: CategoryBreakdown[];
}

export function ExpenseChart({ data }: ExpenseChartProps) {
  const chartData = data
    .filter((cat) => parseFloat(cat.total) > 0)
    .map((cat) => ({
      name: cat.category.charAt(0).toUpperCase() + cat.category.slice(1),
      value: parseFloat(cat.total),
      percentage: cat.percentage,
    }));

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Expense Breakdown</CardTitle>
        </CardHeader>
        <CardContent className="flex h-48 items-center justify-center text-muted-foreground">
          No expense data for this period
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Expense Breakdown</CardTitle>
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
              formatter={(value: number) => [formatCurrency(value), "Amount"]}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
