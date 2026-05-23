import { z } from "zod";

const CATEGORIES = [
  "food", "transport", "utilities", "supplies", "marketing",
  "payroll", "rent", "equipment", "sales", "services", "other", "uncategorized",
] as const;

export const createTransactionSchema = z.object({
  description: z
    .string()
    .min(1, "Description is required")
    .max(500, "Description is too long"),
  amount: z
    .string()
    .min(1, "Amount is required")
    .refine(
      (val) => !isNaN(parseFloat(val)) && parseFloat(val) > 0,
      "Amount must be a positive number",
    ),
  transaction_type: z.enum(["income", "expense"], {
    required_error: "Transaction type is required",
  }),
  transaction_date: z
    .string()
    .min(1, "Date is required")
    .regex(/^\d{4}-\d{2}-\d{2}$/, "Date must be in YYYY-MM-DD format"),
  category: z.enum(CATEGORIES).optional(),
  notes: z.string().max(1000, "Notes are too long").optional(),
});

export const updateTransactionSchema = createTransactionSchema.partial();

export type CreateTransactionFormValues = z.infer<typeof createTransactionSchema>;
export type UpdateTransactionFormValues = z.infer<typeof updateTransactionSchema>;
