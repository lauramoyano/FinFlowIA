import { useMemo } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslation } from "react-i18next";
import {
  useCategories,
  useCreateCategory,
  useDeleteCategory,
} from "@/features/categories/hooks/useCategories";
import {
  createCategorySchema,
  type CreateCategoryFormValues,
} from "@/features/categories/schemas/category.schema";
import type { Category } from "@/features/categories/types/category.types";
import { getCategoryLabel } from "@/features/transactions/lib/category-label";
import { Button } from "@/shared/components/ui/Button";
import { Input } from "@/shared/components/ui/Input";
import { LoadingSpinner } from "@/shared/components/LoadingSpinner";

function CategoryLabel({ category }: { category: Category }) {
  const { t } = useTranslation("transactions");
  return <span>{getCategoryLabel(t, category.name)}</span>;
}

function CategoryColumn({
  title,
  categories,
  isLoading,
  onDelete,
  isDeleting,
}: {
  title: string;
  categories: Category[];
  isLoading: boolean;
  onDelete: (id: string) => void;
  isDeleting: boolean;
}) {
  const { t } = useTranslation("transactions");

  return (
    <div className="flex-1 min-w-[220px]">
      <h3 className="mb-2 text-sm font-semibold text-foreground">{title}</h3>
      {isLoading ? (
        <div className="flex h-24 items-center justify-center">
          <LoadingSpinner size="sm" />
        </div>
      ) : categories.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t("manager.empty")}</p>
      ) : (
        <ul className="space-y-1.5">
          {categories.map((category) => (
            <li
              key={category.id}
              className="flex items-center justify-between rounded-md border bg-card px-3 py-2 text-sm"
            >
              <CategoryLabel category={category} />
              {category.is_default ? (
                <span className="text-xs text-muted-foreground">{t("manager.default")}</span>
              ) : (
                <button
                  type="button"
                  onClick={() => onDelete(category.id)}
                  disabled={isDeleting}
                  className="text-xs font-medium text-destructive hover:underline disabled:opacity-50"
                >
                  {t("list.delete")}
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function CategoryManager() {
  const { t } = useTranslation("transactions");
  const { data: categories = [], isLoading } = useCategories();
  const createMutation = useCreateCategory();
  const deleteMutation = useDeleteCategory();

  const categorySchema = useMemo(() => createCategorySchema(t), [t]);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateCategoryFormValues>({
    resolver: zodResolver(categorySchema),
    defaultValues: { transaction_type: "expense" },
  });

  const expenseCategories = categories.filter((c) => c.transaction_type === "expense");
  const incomeCategories = categories.filter((c) => c.transaction_type === "income");

  const onSubmit = (data: CreateCategoryFormValues) => {
    createMutation.mutate(data, { onSuccess: () => reset({ transaction_type: data.transaction_type, name: "" }) });
  };

  return (
    <div className="rounded-lg border bg-card p-6" data-testid="category-manager">
      <h2 className="mb-1 text-lg font-semibold">{t("manager.title")}</h2>
      <p className="mb-4 text-sm text-muted-foreground">{t("manager.subtitle")}</p>

      <div className="flex flex-wrap gap-6">
        <CategoryColumn
          title={t("list.expense")}
          categories={expenseCategories}
          isLoading={isLoading}
          onDelete={(id) => deleteMutation.mutate(id)}
          isDeleting={deleteMutation.isPending}
        />
        <CategoryColumn
          title={t("list.income")}
          categories={incomeCategories}
          isLoading={isLoading}
          onDelete={(id) => deleteMutation.mutate(id)}
          isDeleting={deleteMutation.isPending}
        />
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-6 flex flex-wrap items-end gap-3 border-t pt-4">
        <Input
          label={t("manager.newCategoryLabel")}
          placeholder={t("manager.newCategoryPlaceholder")}
          error={errors.name?.message}
          {...register("name")}
        />

        <div className="min-w-[140px]">
          <label className="text-sm font-medium">{t("form.typeLabel")}</label>
          <select
            {...register("transaction_type")}
            className="mt-1 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="expense">{t("list.expense")}</option>
            <option value="income">{t("list.income")}</option>
          </select>
        </div>

        <Button type="submit" isLoading={createMutation.isPending}>
          {t("manager.addCategory")}
        </Button>
      </form>

      {createMutation.isError && (
        <p className="mt-2 text-sm text-destructive">{t("manager.createError")}</p>
      )}
    </div>
  );
}
