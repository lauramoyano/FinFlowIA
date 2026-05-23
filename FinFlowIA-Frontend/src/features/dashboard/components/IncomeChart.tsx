import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/Card";
import { formatCurrency } from "@/shared/lib/utils";
import type { CategoryBreakdown } from "@/features/dashboard/api/dashboard.api";

interface IncomeChartProps {
  incomeCategories: CategoryBreakdown[];
}

export function IncomeChart({ incomeCategories }: IncomeChartProps) {
  const chartData = incomeCategories
    .filter((cat) => parseFloat(cat.total) > 0)
    .map((cat) => ({
      name: cat.category.charAt(0).toUpperCase() + cat.category.slice(1),
      amount: parseFloat(cat.total),
    }));

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Income Sources</CardTitle>
        </CardHeader>
        <CardContent className="flex h-48 items-center justify-center text-muted-foreground">
          No income data for this period
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Income Sources</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis dataKey="name" className="text-xs" />
            <YAxis
              className="text-xs"
              tickFormatter={(value: number) =>
                new Intl.NumberFormat("es-AR", {
                  notation: "compact",
                  compactDisplay: "short",
                }).format(value)
              }
            />
            <Tooltip formatter={(value: number) => [formatCurrency(value), "Amount"]} />
            <Bar dataKey="amount" fill="#10b981" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
