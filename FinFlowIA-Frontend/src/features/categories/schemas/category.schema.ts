import { z } from "zod";
import type { TFunction } from "i18next";

/**
 * Built at render time so validation messages come from the "transactions"
 * i18n namespace (categories live inside that feature).
 */
export function createCategorySchema(t: TFunction<"transactions">) {
  return z.object({
    name: z
      .string()
      .min(1, t("manager.validation.nameRequired"))
      .max(50, t("manager.validation.nameTooLong")),
    transaction_type: z.enum(["income", "expense"], {
      required_error: t("manager.validation.typeRequired"),
    }),
  });
}

export type CreateCategoryFormValues = z.infer<ReturnType<typeof createCategorySchema>>;
