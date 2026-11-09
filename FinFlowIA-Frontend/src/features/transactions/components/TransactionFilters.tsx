import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { useCategories } from "@/features/categories/hooks/useCategories";
import { getCategoryLabel } from "@/features/transactions/lib/category-label";
import { Button } from "@/shared/components/ui/Button";
import { Input } from "@/shared/components/ui/Input";
import type { TransactionFilters } from "@/features/transactions/types/transaction.types";

interface TransactionFiltersProps {
  onFilter: (filters: TransactionFilters) => void;
  onReset: () => void;
}

export function TransactionFiltersBar({ onFilter, onReset }: TransactionFiltersProps) {
  const { register, handleSubmit, reset } = useForm<TransactionFilters>();
  const { t } = useTranslation("transactions");
  // Filter dropdown isn't scoped to a single type, so fetch every category
  // the user can see (defaults + their own custom ones) across both types.
  const { data: categories = [] } = useCategories();

  const onSubmit = (data: TransactionFilters) => {
    // Remove empty values
    const cleaned = Object.fromEntries(
      Object.entries(data).filter(([, v]) => v !== "" && v !== undefined),
    ) as TransactionFilters;
    onFilter(cleaned);
  };

  const handleReset = () => {
    reset();
    onReset();
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="flex flex-wrap gap-3 rounded-lg border bg-card p-4"
    >
      <div className="flex min-w-[140px] flex-col gap-1">
        <label className="text-sm font-medium leading-none">{t("filters.typeLabel")}</label>
        <select
          {...register("transaction_type")}
          className="flex h-10 w-full rounded-md border border-input bg-background py-2 pl-3 pr-8 text-sm"
        >
          <option value="">{t("filters.allTypes")}</option>
          <option value="income">{t("list.income")}</option>
          <option value="expense">{t("list.expense")}</option>
        </select>
      </div>

      <div className="flex min-w-[140px] flex-col gap-1">
        <label className="text-sm font-medium leading-none">{t("filters.categoryLabel")}</label>
        <select
          {...register("category")}
          className="flex h-10 w-full rounded-md border border-input bg-background py-2 pl-3 pr-8 text-sm"
        >
          <option value="">{t("filters.allCategories")}</option>
          {categories
            .filter((category) => category.name !== "uncategorized")
            .map((category) => (
              <option key={category.id} value={category.name}>
                {getCategoryLabel(t, category.name)}
              </option>
            ))}
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
        <Button type="submit" size="sm" data-testid="apply-filters-button">
          {t("filters.apply")}
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleReset}
          data-testid="reset-filters-button"
        >
          {t("filters.reset")}
        </Button>
      </div>
    </form>
  );
}
