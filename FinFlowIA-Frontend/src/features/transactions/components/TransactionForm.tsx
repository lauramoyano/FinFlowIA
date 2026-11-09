import { useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslation } from "react-i18next";
import {
  createTransactionSchema,
  type CreateTransactionFormValues,
} from "@/features/transactions/schemas/transaction.schema";
import { useCreateTransaction } from "@/features/transactions/hooks/useCreateTransaction";
import { useCategories } from "@/features/categories/hooks/useCategories";
import { getCategoryLabel } from "@/features/transactions/lib/category-label";
import { Button } from "@/shared/components/ui/Button";
import { Input } from "@/shared/components/ui/Input";
import type { Transaction } from "@/features/transactions/types/transaction.types";

interface TransactionFormProps {
  onSuccess?: (transaction: Transaction) => void;
  onCancel?: () => void;
  // Pre-fills the form — used when the user clicks "Editar" on a chat-parsed
  // transaction (see TransactionChatInput) instead of typing from scratch.
  defaultValues?: Partial<CreateTransactionFormValues>;
}

export function TransactionForm({ onSuccess, onCancel, defaultValues }: TransactionFormProps) {
  const createMutation = useCreateTransaction();
  const { t } = useTranslation("transactions");
  const { t: tCommon } = useTranslation("common");
  const transactionSchema = useMemo(() => createTransactionSchema(t), [t]);

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<CreateTransactionFormValues>({
    resolver: zodResolver(transactionSchema),
    defaultValues: {
      transaction_date: new Date().toISOString().split("T")[0],
      transaction_type: "expense",
      ...defaultValues,
    },
  });

  // Categories are scoped to income vs. expense, so refetch (cached by
  // TanStack Query) whenever the user flips the type dropdown.
  const selectedType = watch("transaction_type");
  const { data: categories = [] } = useCategories(selectedType);

  // The category <select> only has a matching <option> once `categories`
  // finishes loading. If a defaultValues.category was passed (pre-filling
  // from a chat-parsed transaction) and categories were still loading at
  // mount, the browser silently falls back to the first option ("let AI
  // categorize") since no <option> existed yet — re-apply it once the real
  // option exists.
  useEffect(() => {
    if (defaultValues?.category && categories.some((c) => c.name === defaultValues.category)) {
      setValue("category", defaultValues.category);
    }
  }, [categories]);

  const onSubmit = (data: CreateTransactionFormValues) => {
    createMutation.mutate(data, {
      onSuccess: (transaction) => {
        reset();
        onSuccess?.(transaction);
      },
    });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {createMutation.isError && (
        <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
          {t("form.createError")}
        </div>
      )}

      <Input
        label={t("form.descriptionLabel")}
        placeholder={t("form.descriptionPlaceholder")}
        error={errors.description?.message}
        data-testid="description-input"
        {...register("description")}
      />

      <Input
        label={t("form.amountLabel")}
        type="number"
        step="0.01"
        min="0.01"
        placeholder="0.00"
        error={errors.amount?.message}
        {...register("amount")}
      />

      <div>
        <label className="text-sm font-medium">{t("form.typeLabel")}</label>
        <select
          {...register("transaction_type")}
          name="type"
          className="mt-1 flex h-10 w-full rounded-md border border-input bg-background py-2 pl-3 pr-8 text-sm"
        >
          <option value="expense">{t("list.expense")}</option>
          <option value="income">{t("list.income")}</option>
        </select>
        {errors.transaction_type && (
          <p className="text-sm text-destructive">{errors.transaction_type.message}</p>
        )}
      </div>

      <Input
        label={t("form.dateLabel")}
        type="date"
        error={errors.transaction_date?.message}
        {...register("transaction_date")}
      />

      <div>
        <label className="text-sm font-medium">{t("form.categoryLabel")}</label>
        <select
          {...register("category")}
          className="mt-1 flex h-10 w-full rounded-md border border-input bg-background py-2 pl-3 pr-8 text-sm"
        >
          <option value="">{t("form.categoryAiOption")}</option>
          {categories
            .filter((category) => !category.is_default || category.name !== "uncategorized")
            .map((category) => (
              <option key={category.id} value={category.name}>
                {getCategoryLabel(t, category.name)}
              </option>
            ))}
        </select>
      </div>

      <Input
        label={t("form.notesLabel")}
        placeholder={t("form.notesPlaceholder")}
        error={errors.notes?.message}
        {...register("notes")}
      />

      <div className="flex gap-3 pt-2">
        <Button type="submit" isLoading={createMutation.isPending}>
          {t("form.submit")}
        </Button>
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            {tCommon("actions.cancel")}
          </Button>
        )}
      </div>
    </form>
  );
}
