import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/Card";
import { formatCurrency } from "@/shared/lib/utils";

interface SummaryCardsProps {
  totalIncome: string;
  totalExpenses: string;
  balance: string;
  periodLabel: string;
}

export function SummaryCards({
  totalIncome,
  totalExpenses,
  balance,
  periodLabel,
}: SummaryCardsProps) {
  const balanceNum = parseFloat(balance);
  const isPositive = balanceNum >= 0;

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Total Income
          </CardTitle>
          <svg className="h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
          </svg>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold text-green-600">
            {formatCurrency(totalIncome)}
          </p>
          <p className="text-xs text-muted-foreground">{periodLabel}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Total Expenses
          </CardTitle>
          <svg className="h-4 w-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 13l-5 5m0 0l-5-5m5 5V6" />
          </svg>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold text-red-600">
            {formatCurrency(totalExpenses)}
          </p>
          <p className="text-xs text-muted-foreground">{periodLabel}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Net Balance
          </CardTitle>
          <svg className={`h-4 w-4 ${isPositive ? "text-green-500" : "text-red-500"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </CardHeader>
        <CardContent>
          <p className={`text-2xl font-bold ${isPositive ? "text-green-600" : "text-red-600"}`}>
            {isPositive ? "+" : ""}{formatCurrency(balance)}
          </p>
          <p className="text-xs text-muted-foreground">{periodLabel}</p>
        </CardContent>
      </Card>
    </div>
  );
}
