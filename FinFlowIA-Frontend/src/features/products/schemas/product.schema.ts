import { z } from "zod";
import type { TFunction } from "i18next";

/** Built at render time so validation messages come from the "products" i18n namespace. */
export function createProductSchema(t: TFunction<"products">) {
  return z.object({
    name: z
      .string()
      .min(1, t("form.validation.nameRequired"))
      .max(150, t("form.validation.nameTooLong")),
    unit_label: z.string().max(30, t("form.validation.unitLabelTooLong")).optional(),
    unit_insumos_cost: z
      .string()
      .min(1, t("form.validation.costRequired"))
      .refine((v) => !Number.isNaN(Number(v)) && Number(v) >= 0, {
        message: t("form.validation.costMustBePositive"),
      }),
    unit_sale_price: z
      .string()
      .min(1, t("form.validation.salePriceRequired"))
      .refine((v) => !Number.isNaN(Number(v)) && Number(v) >= 0, {
        message: t("form.validation.salePriceMustBePositive"),
      }),
  });
}

export type CreateProductFormValues = z.infer<ReturnType<typeof createProductSchema>>;
