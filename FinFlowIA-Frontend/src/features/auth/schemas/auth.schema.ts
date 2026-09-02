import { z } from "zod";
import type { TFunction } from "i18next";

/**
 * Schemas are built at render time (see useLoginSchema/useRegisterSchema)
 * so validation messages come from the "auth" i18n namespace and update
 * immediately if the user switches language.
 */
export function createLoginSchema(t: TFunction<"auth">) {
  return z.object({
    email: z
      .string()
      .min(1, t("validation.emailRequired"))
      .email(t("validation.emailInvalid")),
    password: z.string().min(1, t("validation.passwordRequired")),
  });
}

export function createRegisterSchema(t: TFunction<"auth">) {
  return z
    .object({
      full_name: z
        .string()
        .min(1, t("validation.fullNameRequired"))
        .max(255, t("validation.fullNameTooLong")),
      email: z
        .string()
        .min(1, t("validation.emailRequired"))
        .email(t("validation.emailInvalid")),
      password: z
        .string()
        .min(8, t("validation.passwordTooShort"))
        .max(128, t("validation.passwordTooLong")),
      confirmPassword: z.string().min(1, t("validation.confirmPasswordRequired")),
    })
    .refine((data) => data.password === data.confirmPassword, {
      message: t("validation.passwordsDoNotMatch"),
      path: ["confirmPassword"],
    });
}

export type LoginFormValues = z.infer<ReturnType<typeof createLoginSchema>>;
export type RegisterFormValues = z.infer<ReturnType<typeof createRegisterSchema>>;
