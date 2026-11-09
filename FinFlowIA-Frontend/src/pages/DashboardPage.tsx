import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useDashboardCharts } from "@/features/dashboard/hooks/useDashboard";
import { SummaryCards } from "@/features/dashboard/components/SummaryCards";
import { ExpenseChart } from "@/features/dashboard/components/ExpenseChart";
import { IncomeChart } from "@/features/dashboard/components/IncomeChart";
import { IncomeVsExpenseChart } from "@/features/dashboard/components/IncomeVsExpenseChart";
import { CombinedChart } from "@/features/dashboard/components/CombinedChart";
import { TrendLineChart } from "@/features/dashboard/components/TrendLineChart";
import { WaterfallChart } from "@/features/dashboard/components/WaterfallChart";
import { CategoryBreakdownList } from "@/features/dashboard/components/CategoryBreakdown";
import { DashboardFiltersBar } from "@/features/dashboard/components/DashboardFiltersBar";
import { ChartHighlightProvider } from "@/features/dashboard/context/ChartHighlightContext";
import { LoadingSpinner } from "@/shared/components/LoadingSpinner";
import type { DashboardChartFilters } from "@/features/dashboard/types/dashboard-filters.types";

function toDateString(d: Date): string {
  return d.toISOString().split("T")[0];
}

function defaultChartFilters(): DashboardChartFilters {
  const end = new Date();
  const start = new Date();
  start.setMonth(start.getMonth() - 5);
  start.setDate(1);
  return {
    granularity: "month",
    start_date: toDateString(start),
    end_date: toDateString(end),
  };
}

export function DashboardPage() {
  const { t, i18n } = useTranslation("dashboard");

  const [chartFilters, setChartFilters] = useState<DashboardChartFilters>(defaultChartFilters);
  const { data: chartsData, isLoading, error } = useDashboardCharts(chartFilters);

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !chartsData) {
    return (
      <div className="rounded-md bg-destructive/10 p-4 text-destructive">
        {t("loadError")}
      </div>
    );
  }

  const locale = i18n.language === "en" ? "en-US" : "es-AR";
  const dateFormatter = new Intl.DateTimeFormat(locale, { day: "numeric", month: "short", year: "numeric" });
  const periodLabel = `${dateFormatter.format(new Date(`${chartsData.start_date}T00:00:00`))} – ${dateFormatter.format(new Date(`${chartsData.end_date}T00:00:00`))}`;

  const totalIncome = chartsData.by_category
    .filter((cat) => cat.transaction_type === "income")
    .reduce((sum, cat) => sum + parseFloat(cat.total), 0);
  const totalExpenses = chartsData.by_category
    .filter((cat) => cat.transaction_type === "expense")
    .reduce((sum, cat) => sum + parseFloat(cat.total), 0);
  const balance = totalIncome - totalExpenses;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold" data-testid="page-title">{t("title")}</h1>
        <p className="text-muted-foreground">{t("overviewFor", { period: periodLabel })}</p>
      </div>

      <SummaryCards
        totalIncome={String(totalIncome)}
        totalExpenses={String(totalExpenses)}
        balance={String(balance)}
        periodLabel={periodLabel}
      />

      <DashboardFiltersBar defaultValues={chartFilters} onFilter={setChartFilters} />

      <ChartHighlightProvider>
        <div className="grid gap-6 lg:grid-cols-2">
          <ExpenseChart
            data={chartsData.by_category.filter((cat) => cat.transaction_type === "expense")}
          />
          <IncomeChart
            incomeCategories={chartsData.by_category.filter(
              (cat) => cat.transaction_type === "income",
            )}
          />
          <IncomeVsExpenseChart timeSeries={chartsData.time_series} />
          <CombinedChart timeSeries={chartsData.time_series} />
          <TrendLineChart timeSeries={chartsData.time_series} />
          <WaterfallChart byCategory={chartsData.by_category} />
        </div>
      </ChartHighlightProvider>

      <CategoryBreakdownList categories={chartsData.by_category} />
    </div>
  );
}
