import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Button } from "@/shared/components/ui/Button";
import { Input } from "@/shared/components/ui/Input";
import type { DashboardChartFilters } from "@/features/dashboard/types/dashboard-filters.types";

interface DashboardFiltersBarProps {
  defaultValues: DashboardChartFilters;
  onFilter: (filters: DashboardChartFilters) => void;
}

export function DashboardFiltersBar({ defaultValues, onFilter }: DashboardFiltersBarProps) {
  const { register, handleSubmit } = useForm<DashboardChartFilters>({ defaultValues });
  const { t } = useTranslation("dashboard");

  return (
    <form
      onSubmit={handleSubmit(onFilter)}
      className="flex flex-wrap gap-3 rounded-lg border bg-card p-4"
    >
      <div className="flex min-w-[140px] flex-col gap-1">
        <label className="text-sm font-medium leading-none">{t("filters.granularityLabel")}</label>
        <select
          {...register("granularity")}
          className="flex h-10 w-full rounded-md border border-input bg-background py-2 pl-3 pr-8 text-sm"
        >
          <option value="day">{t("filters.granularityDay")}</option>
          <option value="month">{t("filters.granularityMonth")}</option>
          <option value="year">{t("filters.granularityYear")}</option>
        </select>
      </div>

      <Input
        label={t("filters.fromLabel")}
        type="date"
        className="min-w-[140px]"
        {...register("start_date")}
      />

      <Input
        label={t("filters.toLabel")}
        type="date"
        className="min-w-[140px]"
        {...register("end_date")}
      />

      <div className="flex items-end gap-2">
        <Button type="submit" size="sm" data-testid="apply-chart-filters-button">
          {t("filters.apply")}
        </Button>
      </div>
    </form>
  );
}
