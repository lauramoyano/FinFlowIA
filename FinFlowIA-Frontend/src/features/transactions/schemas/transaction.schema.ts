import { z } from "zod";
import type { TFunction } from "i18next";

/**
 * Built at render time so validation messages come from the "transactions"
 * i18n namespace (see useMemo(() => createTransactionSchema(t), [t]) in
 * TransactionForm).
 */
export function createTransactionSchema(t: TFunction<"transactions">) {
  return z.object({
    description: z
      .string()
      .min(1, t("form.validation.descriptionRequired"))
      .max(500, t("form.validation.descriptionTooLong")),
    amount: z
      .string()
      .min(1, t("form.validation.amountRequired"))
      .refine(
        (val) => !isNaN(parseFloat(val)) && parseFloat(val) > 0,
        t("form.validation.amountMustBePositive"),
      ),
    transaction_type: z.enum(["income", "expense"], {
      required_error: t("form.validation.typeRequired"),
    }),
    transaction_date: z
      .string()
      .min(1, t("form.validation.dateRequired"))
      .regex(/^\d{4}-\d{2}-\d{2}$/, t("form.validation.dateFormat")),
    // Free-text: can be one of the fixed defaults or any custom category
    // name the user created (see features/categories). Empty string means
    // "let the AI categorize it" (see TransactionForm's categoryAiOption).
    category: z.string().max(50, t("form.validation.categoryTooLong")).optional(),
    notes: z.string().max(1000, t("form.validation.notesTooLong")).optional(),
  });
}

export function createUpdateTransactionSchema(t: TFunction<"transactions">) {
  return createTransactionSchema(t).partial();
}

export type CreateTransactionFormValues = z.infer<ReturnType<typeof createTransactionSchema>>;
export type UpdateTransactionFormValues = z.infer<ReturnType<typeof createUpdateTransactionSchema>>;
