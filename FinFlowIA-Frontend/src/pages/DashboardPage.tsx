import { useDashboard } from "@/features/dashboard/hooks/useDashboard";
import { SummaryCards } from "@/features/dashboard/components/SummaryCards";
import { ExpenseChart } from "@/features/dashboard/components/ExpenseChart";
import { IncomeChart } from "@/features/dashboard/components/IncomeChart";
import { CategoryBreakdownList } from "@/features/dashboard/components/CategoryBreakdown";
import { LoadingSpinner } from "@/shared/components/LoadingSpinner";

export function DashboardPage() {
  const { data, isLoading, error } = useDashboard();

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-md bg-destructive/10 p-4 text-destructive">
        Failed to load dashboard data. Please try again.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">Overview for {data.period_label}</p>
      </div>

      <SummaryCards
        totalIncome={data.total_income}
        totalExpenses={data.total_expenses}
        balance={data.balance}
        periodLabel={data.period_label}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <ExpenseChart data={data.by_category} />
        <IncomeChart incomeCategories={data.by_category.filter(
          (cat) => ["sales", "services"].includes(cat.category)
        )} />
      </div>

      <CategoryBreakdownList categories={data.by_category} />
    </div>
  );
}
